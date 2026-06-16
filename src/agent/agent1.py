"""
Agent 1 — Explorateur d'ontologie (pipeline économe en tokens).

Objectif : produire taxonomy_for_agent_2.json, un fichier qui permet à un
second agent (qui ne connaît PAS le .owl) de requêter proprement le graphe
(classes, URIs, hiérarchie, relations domain/range, individus de vocabulaire).

Pipeline en 3 phases :
  1. Python (owlready2) extrait TOUTE la structure de façon déterministe.
     → 0 risque d'hallucination d'URI, les faits durs sont la propriété de Python.
  2. UN seul appel LLM reçoit uniquement les NOMS et renvoie ceux pertinents
     pour le cas d'usage (recommandation de ressources gamifiées).
     → coût minime (~1 appel, noms seuls), le LLM ne voit jamais une URI.
  3. Python reconstruit le JSON final avec les seuls éléments gardés, en
     garantissant l'intégrité du graphe (ancêtres + classes domain/range).

Si le LLM est indisponible (clé manquante, rate limit), un repli déterministe
basé sur les namespaces produit quand même un JSON exploitable.
"""

import re
import json
from collections import defaultdict
from owlready2 import get_ontology, ThingClass, And, Or, Restriction, sync_reasoner_pellet

from ..config import GROQ_CURATION_MODEL
from ..tools.sparql_tools import ONTOLOGY_PATH, INFERRED_PATH, SWRL_BUILTIN_OPS

# Le JSON de taxonomie est écrit à la racine du projet (../../ depuis l'ontologie).
OUTPUT_PATH = ONTOLOGY_PATH.parents[1] / "taxonomy_for_agent_2.json"

# Ontologie chargée de façon paresseuse : importer ce module ne lit pas le .owl.
_onto = None


def _get_onto():
    """Charge l'ontologie OWL (owlready2) à la première demande."""
    global _onto
    if _onto is None:
        # owlready2 veut un chemin de fichier brut (pas une URI file://).
        # as_posix() donne des slashes avant, OK sous Windows comme Unix.
        _onto = get_ontology(ONTOLOGY_PATH.as_posix()).load()
    return _onto


def run_reasoner():
    """
    Lance le raisonneur Pellet UNE seule fois et sauvegarde l'ontologie enrichie
    (faits déduits) dans TGC_inferred.owl. Ensuite, l'Agent 2 interroge ce fichier
    (via sparql_tools) sans relancer le raisonneur à chaque fois.

    Pellet (et non HermiT) : les règles SWRL de recommandation entre enseignants
    utilisent des built-in atoms (ex: swrlb:greaterThan pour « plus expert que »),
    que HermiT ne sait pas traiter. Pellet les supporte et matérialise donc
    potentialMentorOf / hasSimilarProfile / hasSimilarDomain.

    ATTENTION Java : les jars Pellet/Jena embarqués par owlready2 >= 0.50 sont
    compilés pour un JDK récent (Java 25). Avec un JRE plus ancien (ex: Java 8),
    l'appel lève OwlReadyJavaError. Dans ce cas, l'ontologie de travail contient
    déjà les relations SWRL matérialisées via Protégé/Drools : il suffit de
    re-sauvegarder TGC_inferred.owl depuis ONTOLOGY_PATH (sans raisonneur), ou
    de laisser le loader retomber sur ONTOLOGY_PATH si le fichier inféré est absent.
    """
    onto = _get_onto()
    with onto:
        sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)
    onto.save(file=str(INFERRED_PATH), format="rdfxml")
    print(f"Ontologie enrichie sauvegardée : {INFERRED_PATH}")

# Classes que l'on garde TOUJOURS : socle minimal du cas d'usage. Sert de
# garde-fou si le LLM renvoie une réponse appauvrie. Le LLM décide du reste.
ANCHOR_CLASSES = {
    "Teacher", "Learner", "Person", "Course", "OnlineCourse", "Lesson",
    "GamifiedResource", "GameElementResource", "CompositeResource", "Resource",
    "PlayerType", "LearningStyle", "Audience", "TopicKnowledge",
    "Objective", "BehaviouralObjective", "PedagogicalObjective", "ClassroomObjective",
    "Experience", "GamificationExperience", "PedagogicalExperience",
    "EducationalTopic", "Digital_Competency",
}

# Préfixes lisibles connus (les autres sont dérivés du namespace).
KNOWN_PREFIXES = {
    "http://www.w3.org/2002/07/owl#": "owl",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://www.w3.org/ns/prov#": "prov",
    "http://rdfs.org/sioc/ns#": "sioc",
}


# ==========================================================================
# HELPERS
# ==========================================================================
def ns_of(iri: str) -> str:
    """Namespace d'un IRI (jusqu'au # ou dernier /)."""
    if "#" in iri:
        return iri.rsplit("#", 1)[0] + "#"
    return iri.rsplit("/", 1)[0] + "/"


def derive_prefix(namespace: str) -> str:
    """Préfixe lisible pour un namespace (tgc, tco, prov, ...)."""
    if namespace in KNOWN_PREFIXES:
        return KNOWN_PREFIXES[namespace]
    m = re.match(r"http://www\.hds\.utc\.fr/([^/]+)/tbox#", namespace)
    if m:
        return m.group(1)
    return namespace.rstrip("#/").rsplit("/", 1)[-1]


def named_classes(expr):
    """Aplatit une expression de classe (And/Or/Restriction) en classes nommées."""
    out = []
    if expr is None:
        return out
    if isinstance(expr, ThingClass):
        out.append(expr)
    elif isinstance(expr, (And, Or)):
        for c in expr.Classes:
            out.extend(named_classes(c))
    elif isinstance(expr, Restriction):
        out.extend(named_classes(getattr(expr, "value", None)))
    # OneOf (énumération d'individus), Not, datatypes : ignorés ici
    return out


def datatype_name(r) -> str:
    """Nom lisible d'un type de DataProperty."""
    mapping = {str: "string", int: "int", float: "float", bool: "bool"}
    if r in mapping:
        return mapping[r]
    name = getattr(r, "__name__", str(r))
    return "string" if "str" in name.lower() else name


def first_comment(entity):
    comments = list(getattr(entity, "comment", []) or [])
    return str(comments[0]).strip() if comments else None


def extract_rules(onto) -> list:
    """Extrait les regles SWRL de l'ontologie (lecture seule, 0 token).

    Pour chaque regle DL-safe (corps -> tete), on renvoie :
      - label / comment : tels que portes par la regle (rdfs:label, rdfs:comment) ;
        si le label est juste un numero (regles non nommees), on retombe sur le
        nom du predicat de tete ;
      - head_predicate / head_args : predicat et variables de la tete
        (ex: "recommendedResource", ["?t", "?r"]) ;
      - domain / range : classes des arguments de la tete, retrouvees via les
        ClassAtom du corps portant sur les memes variables ;
      - body_predicates : forme lisible des atomes de propriete du corps
        (ex: "containsGameElement(GamifiedResource, GameElementResource)") ;
      - body_predicate_names : memes atomes, juste les noms de predicats (pour
        savoir si Agent 2 a deja interroge toutes les premisses de la regle) ;
      - body_atoms : forme structuree (IRIs + variables) du corps, utilisee par
        verify_rule_premises (agent2.py) pour verifier par requete SPARQL si les
        premisses de la regle sont satisfaites pour des individus precis.

    Ces regles ne sont PAS executees ici (voir run_reasoner) : on lit juste
    leur definition pour que les agents en aval sachent qu'elles existent.
    """
    rules = []
    for r in onto.rules():
        head_atoms = list(r.head)
        if not head_atoms:
            continue
        head = head_atoms[0]
        head_pred = head.property_predicate.name
        head_args = [str(a) for a in head.arguments]

        arg_classes = {}
        body_preds_fmt = []
        body_pred_names = []
        body_atoms = []
        for atom in r.body:
            kind = type(atom).__name__
            if kind == "ClassAtom":
                var = str(atom.arguments[0])
                arg_classes[var] = atom.class_predicate.name
                body_atoms.append({
                    "kind": "class",
                    "var": var,
                    "class_iri": atom.class_predicate.iri,
                })
            elif kind == "IndividualPropertyAtom":
                a, b = (str(x) for x in atom.arguments)
                name = atom.property_predicate.name
                body_pred_names.append(name)
                body_preds_fmt.append(f"{name}({arg_classes.get(a, a)}, {arg_classes.get(b, b)})")
                body_atoms.append({
                    "kind": "object_property",
                    "subject": a,
                    "object": b,
                    "predicate_iri": atom.property_predicate.iri,
                    "predicate_name": name,
                })
            elif kind == "DatavaluedPropertyAtom":
                a, b = (str(x) for x in atom.arguments)
                body_atoms.append({
                    "kind": "data_property",
                    "subject": a,
                    "value": b,
                    "predicate_iri": atom.property_predicate.iri,
                    "predicate_name": atom.property_predicate.name,
                })
            elif kind == "BuiltinAtom":
                if atom.builtin in SWRL_BUILTIN_OPS:
                    body_atoms.append({
                        "kind": "builtin",
                        "builtin": atom.builtin,
                        "args": [str(x) for x in atom.arguments],
                    })
            elif kind == "DifferentIndividualsAtom":
                body_atoms.append({
                    "kind": "different",
                    "args": [str(x) for x in atom.arguments],
                })

        domain = arg_classes.get(head_args[0], "?")
        range_ = arg_classes.get(head_args[1], "?") if len(head_args) > 1 else None

        label = r.label[0] if r.label else None
        if not label or str(label).isdigit():
            label = head_pred

        rules.append({
            "label": str(label),
            "comment": r.comment[0] if r.comment else None,
            "head_predicate": head_pred,
            "head_args": head_args,
            "domain": domain,
            "range": range_,
            "body_predicates": body_preds_fmt,
            "body_predicate_names": body_pred_names,
            "body_atoms": body_atoms,
        })
    return rules


# ==========================================================================
# PHASE 1 — EXTRACTION DÉTERMINISTE (0 token)
# ==========================================================================
def extract_structure() -> dict:
    """Extrait toute la structure de l'ontologie en dicts purs (URIs incluses)."""
    onto = _get_onto()
    prefixes = {}

    def record_ns(iri):
        ns = ns_of(iri)
        prefixes.setdefault(derive_prefix(ns), ns)

    classes = []
    for c in onto.classes():
        record_ns(c.iri)
        parents = [p for p in c.is_a if isinstance(p, ThingClass) and p is not c]
        subs = [s for s in c.subclasses() if isinstance(s, ThingClass)]
        classes.append({
            "name": c.name,
            "uri": c.iri,
            "prefixed": f"{derive_prefix(ns_of(c.iri))}:{c.name}",
            "parents": [p.iri for p in parents],
            "subclasses": [s.iri for s in subs],
            "comment": first_comment(c),
        })

    object_properties = []
    for p in onto.object_properties():
        record_ns(p.iri)
        domain = {d.iri for d in sum((named_classes(x) for x in p.domain), [])}
        rng = {r.iri for r in sum((named_classes(x) for x in p.range), [])}
        object_properties.append({
            "name": p.name,
            "uri": p.iri,
            "prefixed": f"{derive_prefix(ns_of(p.iri))}:{p.name}",
            "domain": sorted(domain),
            "range": sorted(rng),
            "comment": first_comment(p),
        })

    data_properties = []
    for p in onto.data_properties():
        record_ns(p.iri)
        domain = {d.iri for d in sum((named_classes(x) for x in p.domain), [])}
        datatypes = [datatype_name(r) for r in p.range] or None
        data_properties.append({
            "name": p.name,
            "uri": p.iri,
            "prefixed": f"{derive_prefix(ns_of(p.iri))}:{p.name}",
            "domain": sorted(domain),
            "datatype": datatypes[0] if datatypes else None,
            "comment": first_comment(p),
        })

    # Individus regroupés par classe (décision de curation = 1 par classe)
    individuals_by_class = defaultdict(list)
    for ind in onto.individuals():
        record_ns(ind.iri)
        types = [t for t in ind.is_a if isinstance(t, ThingClass)]
        for t in types:
            individuals_by_class[t.name].append({
                "name": ind.name,
                "uri": ind.iri,
                "types": [tt.iri for tt in types],
            })

    return {
        "ontology_iri": onto.base_iri,
        "prefixes": prefixes,
        "classes": classes,
        "object_properties": object_properties,
        "data_properties": data_properties,
        "individuals_by_class": dict(individuals_by_class),
        "swrl_rules": extract_rules(onto),
    }


# ==========================================================================
# PHASE 2 — CURATION PAR LE LLM (noms seuls, 1 appel)
# ==========================================================================
FILTER_SYSTEM = (
    "You are an ontology curator. Downstream use case: an agent recommends "
    "GamifiedResources (game elements like points, badges, leaderboards, levels) "
    "to a Teacher for a Course, taking into account the Learners' profiles "
    "(player types, learning styles), pedagogical objectives, and topics.\n\n"
    "You receive lists of NAMES extracted from an ontology. Return ONLY the names "
    "relevant to this recommendation use case.\n"
    "KEEP: people (Teacher/Learner), courses/lessons, resources & game elements, "
    "learner & teacher profiles (player type, learning style, experience), "
    "objectives, topics, audiences, competencies, and the properties linking them.\n"
    "DROP generic plumbing: provenance (prov), social/user accounts-groups-spaces (sioc), "
    "CRUD activity logging, indexing / reference keys.\n"
    "For individuals (given grouped by class): keep a class's individuals only if they "
    "are a controlled VOCABULARY (e.g. the 4 PlayerTypes, the BehaviouralObjectives, "
    "learning-style poles) — DROP sample/instance data (named teachers, documents, "
    "reference keys, lessons...).\n\n"
    "Return ONLY a JSON object, no prose:\n"
    '{"keep_classes":[...],"keep_object_properties":[...],'
    '"keep_data_properties":[...],"keep_individual_classes":[...]}'
)


def build_filter_input(structure: dict) -> str:
    """Construit l'entrée LLM : uniquement des noms (économe en tokens)."""
    class_names = [c["name"] for c in structure["classes"]]
    op_names = [p["name"] for p in structure["object_properties"]]
    dp_names = [p["name"] for p in structure["data_properties"]]

    indiv_lines = []
    for cls, inds in sorted(structure["individuals_by_class"].items()):
        names = [i["name"] for i in inds]
        shown = ", ".join(names[:6]) + (f", ... ({len(names)} total)" if len(names) > 6 else "")
        indiv_lines.append(f"  {cls}: {shown}")

    return (
        "CLASSES:\n" + ", ".join(class_names) + "\n\n"
        "OBJECT_PROPERTIES:\n" + ", ".join(op_names) + "\n\n"
        "DATA_PROPERTIES:\n" + ", ".join(dp_names) + "\n\n"
        "INDIVIDUALS (by class — decide which classes' individuals are vocabulary):\n"
        + "\n".join(indiv_lines)
    )


def parse_json_obj(text: str) -> dict:
    """Extrait le premier objet JSON d'une réponse LLM, tolérant aux ```fences."""
    text = text.strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Aucun objet JSON dans la réponse LLM")
    return json.loads(text[start:end + 1])


def curate_with_llm(structure: dict) -> dict:
    """Appel LLM unique. Renvoie les sets de noms à garder, ou lève une exception."""
    # Import paresseux : extract_structure / apply_filter restent utilisables sans le paquet LLM.
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage
    llm = ChatGroq(model=GROQ_CURATION_MODEL, temperature=0)
    messages = [
        SystemMessage(content=FILTER_SYSTEM),
        HumanMessage(content=build_filter_input(structure)),
    ]
    response = llm.invoke(messages)
    parsed = parse_json_obj(response.content)
    return {
        "classes": set(parsed.get("keep_classes", [])),
        "object_properties": set(parsed.get("keep_object_properties", [])),
        "data_properties": set(parsed.get("keep_data_properties", [])),
        "individual_classes": set(parsed.get("keep_individual_classes", [])),
    }


def fallback_keep(structure: dict) -> dict:
    """Repli déterministe : garde les namespaces pédagogiques (tgc, tco)."""
    pedago_ns = {structure["prefixes"].get("tgc"), structure["prefixes"].get("tco")}

    def in_pedago(uri):
        return ns_of(uri) in pedago_ns

    classes = {c["name"] for c in structure["classes"] if in_pedago(c["uri"])}
    ops = {p["name"] for p in structure["object_properties"] if in_pedago(p["uri"])}
    dps = {p["name"] for p in structure["data_properties"] if in_pedago(p["uri"])}
    # Vocabulaire = classes pédagogiques avec peu d'individus (≤ 8)
    indiv_cls = {
        cls for cls, inds in structure["individuals_by_class"].items()
        if len(inds) <= 8 and cls in classes
    }
    return {"classes": classes, "object_properties": ops,
            "data_properties": dps, "individual_classes": indiv_cls}


# ==========================================================================
# PHASE 3 — RECONSTRUCTION + INTÉGRITÉ DU GRAPHE
# ==========================================================================
def apply_filter(structure: dict, keep: dict) -> dict:
    """Reconstruit le JSON final ; garantit l'intégrité (ancêtres + domain/range)."""
    by_uri = {c["uri"]: c for c in structure["classes"]}
    name_to_uri = {c["name"]: c["uri"] for c in structure["classes"]}

    # 1) Classes initiales : sélection LLM ∪ ancres
    kept_uris = set()
    for name in keep["classes"] | ANCHOR_CLASSES:
        if name in name_to_uri:
            kept_uris.add(name_to_uri[name])

    # 2) Propriétés gardées + collecte des classes qu'elles référencent
    kept_ops = [p for p in structure["object_properties"] if p["name"] in keep["object_properties"]]
    kept_dps = [p for p in structure["data_properties"] if p["name"] in keep["data_properties"]]
    for p in kept_ops:
        kept_uris.update(u for u in p["domain"] + p["range"] if u in by_uri)
    for p in kept_dps:
        kept_uris.update(u for u in p["domain"] if u in by_uri)

    # 3) Fermeture sur les ancêtres : ne jamais casser la hiérarchie
    changed = True
    while changed:
        changed = False
        for uri in list(kept_uris):
            for parent in by_uri.get(uri, {}).get("parents", []):
                if parent in by_uri and parent not in kept_uris:
                    kept_uris.add(parent)
                    changed = True

    # 4) Reconstruit les classes (parents/subclasses restreints aux gardées)
    final_classes = []
    for uri in kept_uris:
        c = dict(by_uri[uri])
        c["parents"] = [u for u in c["parents"] if u in kept_uris]
        c["subclasses"] = [u for u in c["subclasses"] if u in kept_uris]
        final_classes.append(c)
    final_classes.sort(key=lambda c: c["name"])

    # 5) Individus de vocabulaire (classe gardée + sélectionnée)
    kept_class_names = {by_uri[u]["name"] for u in kept_uris}
    final_individuals = []
    seen = set()
    for cls in keep["individual_classes"]:
        if cls not in kept_class_names:
            continue
        for ind in structure["individuals_by_class"].get(cls, []):
            if ind["uri"] not in seen:
                seen.add(ind["uri"])
                final_individuals.append({
                    "name": ind["name"], "uri": ind["uri"],
                    "types": [t for t in ind["types"] if t in kept_uris],
                })
    final_individuals.sort(key=lambda i: i["name"])

    # 6) Préfixes effectivement utilisés
    used_ns = {ns_of(c["uri"]) for c in final_classes}
    used_ns |= {ns_of(p["uri"]) for p in kept_ops + kept_dps}
    prefixes = {pfx: ns for pfx, ns in structure["prefixes"].items() if ns in used_ns}

    # Nettoie les commentaires None
    def clean(d):
        return {k: v for k, v in d.items() if v is not None}

    return {
        "ontology_iri": structure["ontology_iri"],
        "prefixes": prefixes,
        "classes": [clean(c) for c in final_classes],
        "object_properties": [clean(p) for p in kept_ops],
        "data_properties": [clean(p) for p in kept_dps],
        "individuals": final_individuals,
        # Regles SWRL : passees telles quelles (liste fixe et courte, pas de
        # curation LLM necessaire) pour qu'Agent 2 sache quelles proprietes
        # sont deduites par le raisonneur (recommendedResource, ...).
        "swrl_rules": structure.get("swrl_rules", []),
    }


# ==========================================================================
# MAIN
# ==========================================================================
if __name__ == "__main__":
    print("Phase 1 — extraction déterministe...")
    structure = extract_structure()
    print(f"  {len(structure['classes'])} classes, "
          f"{len(structure['object_properties'])} object props, "
          f"{len(structure['data_properties'])} data props, "
          f"{sum(len(v) for v in structure['individuals_by_class'].values())} individus, "
          f"{len(structure['swrl_rules'])} regles SWRL")

    print("Phase 2 — curation LLM (noms seuls)...")
    filter_input = build_filter_input(structure)
    print(f"  entrée LLM ≈ {len(filter_input)} chars (~{len(filter_input)//4} tokens)")
    try:
        keep = curate_with_llm(structure)
        print(f"  LLM garde : {len(keep['classes'])} classes, "
              f"{len(keep['object_properties'])} obj props, "
              f"{len(keep['data_properties'])} data props, "
              f"{len(keep['individual_classes'])} classes d'individus")
    except Exception as e:
        print(f"  ⚠ LLM indisponible ({e}) — repli déterministe (namespaces tgc/tco)")
        keep = fallback_keep(structure)

    print("Phase 3 — reconstruction + intégrité...")
    result = apply_filter(structure, keep)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✓ {OUTPUT_PATH} généré : "
          f"{len(result['classes'])} classes, "
          f"{len(result['object_properties'])} object props, "
          f"{len(result['data_properties'])} data props, "
          f"{len(result['individuals'])} individus de vocabulaire, "
          f"{len(result['swrl_rules'])} regles SWRL")

    print("\nPhase 4 — raisonneur (règles SWRL)...")
    try:
        run_reasoner()
    except Exception as e:
        print(f"  ⚠ Raisonneur non exécuté ({e}). Java est-il installé ?")
