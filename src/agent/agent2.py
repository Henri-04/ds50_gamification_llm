"""
Agent 2 — recommandation.

Traduit la question de l'enseignant en requête SPARQL, l'exécute sur l'ontologie
et renvoie les données trouvées. Une petite boucle de retry corrige la requête
si elle est invalide ou ne renvoie rien.
"""

import re

from ..llm.groq_client import call_llm
from ..tools.sparql_tools import run_sparql, run_sparql_ask, PREFIXES, SWRL_BUILTIN_OPS

MAX_RETRIES = 3  # chaque tentative = 1 appel LLM (resume court -> peu de tokens)


_SYSTEM_PROMPT = f"""\
Tu es un generateur de requetes SPARQL pour une ontologie de gamification \
pedagogique (ontologie TGC).

A partir d'un resume de l'ontologie et d'une question, tu produis UNE requete \
SPARQL SELECT qui recupere les donnees reelles permettant de repondre.

Prefixes disponibles (deja declares, tu peux les utiliser directement) :
{PREFIXES}
Regles :
- Reponds UNIQUEMENT par la requete SPARQL, sans explication ni texte autour.
- N'invente aucune entite : utilise exactement les noms presents dans le resume.
- Garde la requete LARGE pour ne rien exclure : mets le type (a/rdf:type) et les
  attributs (titre, description) en OPTIONAL.
- N'utilise JAMAIS de FILTER sur la langue (lang()) : les libelles n'ont pas de tag.
"""


def _build_context(state):
    """Ancre la requête sur l'enseignant et la leçon réellement choisis."""
    teacher = state.get("teacher")
    lesson = state.get("lesson")
    course = state.get("course")
    parts = []
    if teacher:
        parts.append(f"- enseignant : tgc:{teacher}")
    if lesson:
        parts.append(f"- lecon : tgc:{lesson}")
    if course:
        parts.append(f"- cours : {course}")
    if not parts:
        return ""
    return (
        "Contexte — ANCRE ta requete sur ces individus EXACTS :\n" + "\n".join(parts) + "\n"
        "Pour les ressources d'une lecon, fais SIMPLE et LARGE :\n"
        "  tgc:<Lecon> tco:reuseResource ?res . OPTIONAL { ?res tgc:has_title ?title }\n"
        "Mets le type (tgc:GamifiedResource) en OPTIONAL, et PAS de FILTER de langue."
    )


def _build_messages(question, summary, feedback, context=""):
    user = f"Resume de l'ontologie :\n{summary}\n\n"
    if context:
        user += f"{context}\n\n"
    user += f"Question de l'enseignant :\n{question}"
    if feedback:
        user += f"\n\nLa tentative precedente a echoue : {feedback}\nCorrige la requete."
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def _extract_sparql(text):
    """Récupère la requête SPARQL dans la réponse du LLM (enlève le markdown)."""
    fenced = re.search(r"```(?:sparql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    match = re.search(r"(PREFIX|SELECT|ASK|CONSTRUCT)\b", text, re.IGNORECASE)
    if match:
        return text[match.start():].strip()
    return text.strip()


def _format_recommendation(question, rows):
    if not rows:
        return "Aucune donnee correspondante n'a ete trouvee dans l'ontologie pour cette demande."
    lines = [f"{len(rows)} resultat(s) trouve(s) dans l'ontologie :"]
    for row in rows:
        parts = [f"{k}={v}" for k, v in row.items() if v is not None]
        lines.append("  - " + ", ".join(parts))
    return "\n".join(lines)


def generate_and_run(question, summary, context="", max_retries=MAX_RETRIES):
    """Génère une requête SPARQL, l'exécute, et réessaie si invalide ou vide."""
    feedback = None
    last_query = ""
    last_rows = []
    for attempt in range(1, max_retries + 1):
        reponse = call_llm(_build_messages(question, summary, feedback, context))
        last_query = _extract_sparql(reponse)
        try:
            last_rows = run_sparql(last_query)
        except Exception as exc:  # requête invalide -> on renvoie l'erreur au LLM
            feedback = f"erreur de syntaxe SPARQL : {exc}"
            continue
        if last_rows:
            return {"sparql_query": last_query, "query_results": last_rows,
                    "attempts": attempt, "error": None}
        feedback = "la requete etait valide mais n'a renvoye aucun resultat."
    return {"sparql_query": last_query, "query_results": last_rows,
            "attempts": max_retries, "error": feedback}


def _swrl_term(value, bindings):
    """Variable SWRL -> tgc:Individu si liée dans `bindings`, sinon variable
    SPARQL inchangée (existentielle) ; valeur littérale (ex: "2") inchangée."""
    if isinstance(value, str) and value.startswith("?"):
        return f"tgc:{bindings[value]}" if value in bindings else value
    return str(value)


def verify_rule_premises(rule, bindings):
    """
    Vérifie si TOUTES les prémisses (corps) de `rule` sont satisfaites pour les
    individus donnés dans `bindings` (ex: {"?t": "Sara", "?r": "GamifiedResource_X"}),
    via une requête SPARQL ASK sur l'ontologie de travail.

    Les variables non liées restent existentielles (ASK cherche une assignation
    qui satisfait le motif). Retourne True/False, ou None si la règle ne porte
    pas de body_atoms structuré (taxonomie générée avant cette fonctionnalité).
    """
    body_atoms = rule.get("body_atoms")
    if not body_atoms:
        return None

    triples, filters = [], []
    for atom in body_atoms:
        kind = atom["kind"]
        if kind == "class":
            term = _swrl_term(atom["var"], bindings)
            triples.append(f"{term} a/rdfs:subClassOf* <{atom['class_iri']}> .")
        elif kind == "object_property":
            s = _swrl_term(atom["subject"], bindings)
            o = _swrl_term(atom["object"], bindings)
            triples.append(f"{s} <{atom['predicate_iri']}> {o} .")
        elif kind == "data_property":
            s = _swrl_term(atom["subject"], bindings)
            v = _swrl_term(atom["value"], bindings)
            triples.append(f"{s} <{atom['predicate_iri']}> {v} .")
        elif kind == "builtin":
            op = SWRL_BUILTIN_OPS.get(atom["builtin"])
            if not op:
                continue
            a, b = (_swrl_term(x, bindings) for x in atom["args"])
            filters.append(f"FILTER({a} {op} {b})")
        elif kind == "different":
            a, b = (_swrl_term(x, bindings) for x in atom["args"])
            filters.append(f"FILTER({a} != {b})")

    if not triples:
        return None

    return run_sparql_ask("ASK { " + " ".join(triples + filters) + " }")


def gather_ontology_facts(state):
    """
    Récupère de façon déterministe un maximum de faits réels sur la leçon choisie
    (ressources, éléments de jeu, objectifs, sujet, profil du prof). Ce texte sert
    de base solide à Agent 3 pour qu'il s'appuie sur l'ontologie, sans inventer.

    Au passage, alimente le state pour la traçabilité :
    - state["links_used"] : les liens (triplets sujet --predicat--> objet)
      effectivement traversés pour construire ces faits ;
    - state["swrl_rules_cited"] : pour chaque fait déduit par le raisonneur SWRL
      (ex: tgc:designedWithObjective, tgc:recommendedResource), la ou les règles
      dont la tête conclut ce prédicat, avec le résultat de
      verify_rule_premises (les prémisses de la règle sont-elles satisfaites
      pour CES individus précis ?). Si plusieurs règles sont vérifiées pour le
      même fait, elles apparaissent toutes : c'est une information utile.
    - state["candidate_resources"] : pour chaque ressource de la leçon (via
      tco:reuseResource), son titre, ses éléments de jeu (avec leurs objectifs)
      et si elle est recommandée pour l'enseignant par le raisonneur SWRL.
      Sert à Agent 3 pour comparer la ressource choisie aux autres candidates.
    """
    lesson = state.get("lesson")
    teacher = state.get("teacher")
    if not lesson:
        return ""

    facts = []
    links = []
    swrl_rules = state.get("swrl_rules") or []
    cited = []
    cited_seen = set()

    def link(subj, pred, obj, note=""):
        suffix = f"  [{note}]" if note else ""
        links.append(f"tgc:{subj} --tgc:{pred}--> tgc:{obj}{suffix}")

    def cite_swrl(head_predicate, domain_value, range_value):
        """Pour chaque règle concluant `head_predicate`, vérifie si ses
        prémisses sont satisfaites pour (domain_value, range_value) et
        enregistre le résultat dans `cited` (pour la traçabilité)."""
        for rule in swrl_rules:
            if rule.get("head_predicate") != head_predicate:
                continue
            key = (rule["label"], domain_value, range_value)
            if key in cited_seen:
                continue
            cited_seen.add(key)
            head_args = rule.get("head_args", [])
            bindings = {}
            if len(head_args) > 0:
                bindings[head_args[0]] = domain_value
            if len(head_args) > 1 and range_value is not None:
                bindings[head_args[1]] = range_value
            verified = verify_rule_premises(rule, bindings)
            cited.append({"rule": rule, "bindings": bindings, "verified": verified})

    # Lien enseignant -> leçon (designLesson) : utilisé par Agent 3 pour le
    # chemin de recommandation (section "Justification du choix de la
    # ressource gamifiée").
    if teacher:
        designed = run_sparql(f"SELECT ?l WHERE {{ tgc:{teacher} tgc:designLesson ?l }}")
        if any(d["l"] == lesson for d in designed):
            link(teacher, "designLesson", lesson)

    # Sujet et leçon préalable
    topics = run_sparql(f"SELECT ?o WHERE {{ tgc:{lesson} tgc:CoversTopic ?o }}")
    if topics:
        facts.append("Sujet : " + ", ".join(t["o"] for t in topics))
        for t in topics:
            link(lesson, "CoversTopic", t["o"])
    pre = run_sparql(f"SELECT ?o WHERE {{ tgc:{lesson} tgc:hasPreLesson ?o }}")
    if pre:
        facts.append("Leçon préalable : " + ", ".join(p["o"] for p in pre))
        for p in pre:
            link(lesson, "hasPreLesson", p["o"])

    # Profil de l'enseignant (ce qu'il aime / son style)
    if teacher:
        pt = run_sparql(f"SELECT ?o WHERE {{ tgc:{teacher} tgc:hasPlayerType ?o }}")
        st = run_sparql(f"SELECT ?o WHERE {{ tgc:{teacher} tgc:has_TeachingStyle ?o }}")
        profil = []
        if pt:
            profil.append("player type = " + ", ".join(x["o"] for x in pt))
            for x in pt:
                link(teacher, "hasPlayerType", x["o"])
        if st:
            profil.append("style = " + ", ".join(x["o"] for x in st))
            for x in st:
                link(teacher, "has_TeachingStyle", x["o"])
        if profil:
            facts.append(f"Profil de l'enseignant {teacher} : " + " ; ".join(profil))

    # Ressources de la leçon + leurs éléments de jeu (type + objectif)
    resources = run_sparql(f"SELECT ?res WHERE {{ tgc:{lesson} tco:reuseResource ?res }}")
    res_lines = []
    candidate_resources = []
    for r in resources:
        res = r["res"]
        links.append(f"tgc:{lesson} --tco:reuseResource--> tgc:{res}")
        titre = run_sparql(f"SELECT ?x WHERE {{ tgc:{res} tgc:has_title ?x }}")
        titre = titre[0]["x"] if titre else res
        elems = []
        game_elements = []
        for e in run_sparql(f"SELECT ?g WHERE {{ tgc:{res} tgc:containsGameElement ?g }}"):
            g = e["g"]
            link(res, "containsGameElement", g)
            types = run_sparql(f"SELECT ?t WHERE {{ tgc:{g} a ?t }}")
            type_ge = next((t["t"] for t in types if "Named" not in t["t"]), "?")
            objs = run_sparql(f"SELECT ?o WHERE {{ tgc:{g} tgc:relevantToObjective ?o }}")
            objectives = [o["o"] for o in objs]
            obj = ", ".join(objectives) or "?"
            for o in objs:
                link(g, "relevantToObjective", o["o"])
                # containsGameElement(res,g) + relevantToObjective(g,o) sont
                # exactement les premisses de la regle "designedWithObjective" :
                # on verifie si elle conclut bien designedWithObjective(res,o).
                cite_swrl("designedWithObjective", res, o["o"])
            elems.append(f"{g} (type {type_ge}, objectif {obj})")
            game_elements.append({"name": g, "type": type_ge, "objectives": objectives})
        ligne = f"- {titre}"
        if elems:
            ligne += " — éléments de jeu : " + " ; ".join(elems)
        res_lines.append(ligne)
        # Une ressource est consideree "gamifiee" (pour la comparaison des
        # candidates, cf. Agent 3) si elle contient au moins un element de jeu :
        # le seul rdf:type tgc:GamifiedResource n'est pas discriminant ici, le
        # raisonneur l'attribue a toutes les ressources composites de la lecon.
        candidate_resources.append({
            "name": res,
            "title": titre,
            "is_gamified": bool(game_elements),
            "game_elements": game_elements,
            "recommended_swrl": False,
        })
    if res_lines:
        facts.append("Ressources de la leçon :\n" + "\n".join(res_lines))

    # Ressources recommandées pour cet enseignant par le raisonneur SWRL
    # (tgc:recommendedResource, déjà matérialisée dans l'ontologie de travail
    # par les règles RecommendResourceByTeacherObjective /
    # RecommendResourceForExperiencedTeacher).
    if teacher and resources:
        recommended = run_sparql(f"SELECT ?r WHERE {{ tgc:{teacher} tgc:recommendedResource ?r }}")
        recommended_names = {x["r"] for x in recommended}
        lesson_res_names = {r["res"] for r in resources}
        overlap = sorted(lesson_res_names & recommended_names)
        for x in overlap:
            link(teacher, "recommendedResource", x, note="deduit par le raisonneur SWRL")
            cite_swrl("recommendedResource", teacher, x)
        for cand in candidate_resources:
            if cand["name"] in overlap:
                cand["recommended_swrl"] = True
        if overlap:
            facts.append(
                f"Ressources de la leçon recommandées pour {teacher} par le "
                "raisonneur SWRL (tgc:recommendedResource) : " + ", ".join(overlap)
            )

    if not facts:
        return ""

    state["links_used"] = links
    state["swrl_rules_cited"] = cited
    state["candidate_resources"] = candidate_resources
    return "FAITS DE L'ONTOLOGIE (à utiliser tels quels, ne rien inventer) :\n" + "\n".join(facts)


def recommend(state):
    """Nœud Agent 2 : remplit sparql_query, query_results, recommendation, ontology_facts."""
    question = state.get("user_input", "")
    summary = state.get("ontology_summary") or "(aucun resume fourni)"
    context = _build_context(state)
    result = generate_and_run(question, summary, context=context)
    state["sparql_query"] = result["sparql_query"]
    state["query_results"] = result["query_results"]
    state["attempts"] = result["attempts"]
    state["recommendation"] = _format_recommendation(question, result["query_results"])
    state["ontology_facts"] = gather_ontology_facts(state)
    state["final_answer"] = state["recommendation"]
    return state


if __name__ == "__main__":
    # Petit test manuel : python -m src.agent.agent2
    summary = "tgc:designLesson : Teacher -> Lesson ; tco:reuseResource : Lesson -> Resource"
    res = generate_and_run(
        "Quelles ressources pour la lecon sur l'heritage ?",
        summary,
        context="- lecon : tgc:Lesson4_Inheritance",
    )
    print("SPARQL :\n", res["sparql_query"])
    print(_format_recommendation("", res["query_results"]))
