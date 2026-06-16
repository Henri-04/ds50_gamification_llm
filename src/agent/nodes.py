"""
Nœuds de la pipeline Agent 1 → Agent 2 → Bridge → Agent 3.

Chaque nœud prend un AgentState et retourne un AgentState enrichi.
"""

import json

from .state import AgentState
from .intent import detect_intent
from ..llm.groq_client import call_llm   # import léger (client Groq paresseux)
from ..tools.sparql_tools import ONTOLOGY_PATH

# agent2 / agent3 sont importés paresseusement dans les nœuds correspondants :
# la branche « personnes » et la détection d'intention restent ainsi utilisables
# sans les paquets LLM (la branche « ressource » les charge à la demande).

# Taxonomie à la racine du projet (../../ depuis l'ontologie).
TAXONOMY_PATH = ONTOLOGY_PATH.parents[1] / "taxonomy_for_agent_2.json"


# =============================================================================
# Nœud 0 — Détection d'intention (recommander une ressource OU des personnes)
# =============================================================================

def node_classify_intent(state: AgentState) -> AgentState:
    """Détermine l'intention de la question et la stocke dans le state."""
    state["intent"] = detect_intent(state.get("user_input", ""))
    print(f"[intent] → {state['intent']}")
    return state


def route_intent(state: AgentState) -> str:
    """Aiguillage LangGraph : 'people' -> recommandation de profs, sinon ressource."""
    return "people" if state.get("intent") == "people" else "resource"


def node_recommend_people(state: AgentState) -> AgentState:
    """Recommande des enseignants (mentors / pairs) à partir de l'ontologie."""
    from .people import recommend_people  # déterministe, pas de dépendance LLM
    print("[Personnes] Recommandation de mentors / pairs (déterministe)...")
    state = recommend_people(state)
    print("[Personnes] ✓ recommandation terminée")
    return state


# =============================================================================
# Nœud 1 — Taxonomie (Agent 1)
# =============================================================================

def _nom_court(uri, prefixes):
    """Transforme une URI en nom court (ex: tgc:Teacher)."""
    for prefixe, ns in prefixes.items():
        if uri.startswith(ns):
            return prefixe + ":" + uri[len(ns):]
    return uri.split("#")[-1]


def _compact_summary(taxonomy):
    """
    Petit résumé texte de l'ontologie pour l'Agent 2 (noms + relations).

    On n'envoie pas toute la taxonomie (trop de tokens -> erreurs 429 de Groq) :
    juste les classes, les relations et le vocabulaire utiles pour écrire du SPARQL.
    """
    prefixes = taxonomy["prefixes"]
    lignes = []

    lignes.append("CLASSES : " + ", ".join(c["prefixed"] for c in taxonomy["classes"]))

    lignes.append("RELATIONS (propriete : domaine -> portee) :")
    for p in taxonomy["object_properties"]:
        domaine = ", ".join(_nom_court(u, prefixes) for u in p.get("domain", [])) or "?"
        portee = ", ".join(_nom_court(u, prefixes) for u in p.get("range", [])) or "?"
        lignes.append("  " + p["prefixed"] + " : " + domaine + " -> " + portee)

    lignes.append("ATTRIBUTS : " + ", ".join(p["prefixed"] for p in taxonomy["data_properties"]))

    individus = taxonomy.get("individuals", [])
    if individus:
        lignes.append("VOCABULAIRE : " + ", ".join(_nom_court(i["uri"], prefixes) for i in individus))

    # Proprietes deduites par le raisonneur SWRL (deja materialisees dans
    # l'ontologie de travail) : Agent 2 peut les interroger directement,
    # comme n'importe quelle autre propriete.
    swrl_rules = taxonomy.get("swrl_rules", [])
    if swrl_rules:
        seen = {}
        for r in swrl_rules:
            seen.setdefault(r["head_predicate"], r)
        lignes.append("RELATIONS DEDUITES PAR LE RAISONNEUR (SWRL, deja materialisees) :")
        for pred, r in seen.items():
            portee = r["range"] or "?"
            commentaire = (r.get("comment") or "").split(".")[0]
            lignes.append(f"  tgc:{pred} : {r['domain']} -> {portee} -- {commentaire}")

    return "\n".join(lignes)


def node_load_taxonomy(state: AgentState) -> AgentState:
    """Charge taxonomy_for_agent_2.json, ou lance Agent 1 pour le générer."""
    print("[Agent 1] Chargement de la taxonomie de l'ontologie...")
    if TAXONOMY_PATH.exists():
        with open(TAXONOMY_PATH, encoding="utf-8") as f:
            taxonomy = json.load(f)
    else:
        print("Agent 1 : taxonomie absente — génération...")
        from .agent1 import extract_structure, curate_with_llm, apply_filter, fallback_keep
        structure = extract_structure()
        try:
            keep = curate_with_llm(structure)
        except Exception as e:
            print(f"Agent 1 : LLM indisponible ({e}) — repli déterministe")
            keep = fallback_keep(structure)
        taxonomy = apply_filter(structure, keep)
        with open(TAXONOMY_PATH, "w", encoding="utf-8") as f:
            json.dump(taxonomy, f, indent=2, ensure_ascii=False)

    state["ontology_summary"] = _compact_summary(taxonomy)
    # Definitions des regles SWRL : transmises telles quelles, pour qu'Agent 2
    # puisse citer les regles dont les conclusions sont effectivement utilisees
    # (cf. _cited_swrl_rules dans agent2.py).
    state["swrl_rules"] = taxonomy.get("swrl_rules", [])
    return state


# =============================================================================
# Nœud 2 — Recommandation (Agent 2)
# =============================================================================

def node_recommend(state: AgentState) -> AgentState:
    """Agent 2 : question NL → SPARQL → recommandation."""
    from .agent2 import recommend
    print("[Agent 2] Génération de la requête SPARQL...")
    state = recommend(state)
    n = len(state.get("query_results") or [])
    print(f"[Agent 2] {n} résultat(s) en {state.get('attempts', '?')} tentative(s)")

    # Aucun ancrage possible (ni résultat SPARQL, ni fait déterministe) : on
    # ABANDONNE explicitement plutôt que de générer une ressource sans fondement.
    if not state.get("query_results") and not state.get("ontology_facts"):
        state["status"] = "no_data"
        lecon = state.get("lesson") or "cette leçon"
        state["final_answer"] = (
            f"Aucune donnée dans l'ontologie ne correspond à cette demande pour « {lecon} ». "
            "Aucune recommandation n'est produite (pas de fabrication)."
        )
        print("[Agent 2] aucun fait exploitable → abandon explicite")
    return state


def route_after_recommend(state: AgentState) -> str:
    """Abandonne si Agent 2 n'a aucun fait à transmettre ; sinon continue vers le Bridge."""
    return "abort" if state.get("status") == "no_data" else "bridge"


# =============================================================================
# Nœud 3 — Bridge LLM
# =============================================================================

_BRIDGE_SYSTEM = """\
Tu es un expert en gamification pédagogique.
À partir d'une question enseignant, d'une leçon et d'une recommandation,
extrais les champs nécessaires pour générer une ressource gamifiée.

Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour :
{
  "learner_profile": "description courte du profil apprenant visé",
  "pedagogical_objective": "objectif pédagogique principal de la leçon",
  "behavioural_objective": "un parmi : Motivation, Participation, Exploration, Group_Learning, Performance",
  "recommended_game_element": "élément de jeu concret (ex: Quiz, Badge, Leaderboard, Progress Bar, Défi...)",
  "recommended_resource_type": "type de ressource (ex: activité interactive, défi chronométré, parcours...)"
}"""

# Champs produits par le Bridge à partir des faits réels. AUCUNE valeur n'est
# fabriquée : si le LLM ne les fournit pas, le Bridge échoue explicitement.
_BRIDGE_FIELDS = (
    "learner_profile",
    "pedagogical_objective",
    "behavioural_objective",
    "recommended_game_element",
    "recommended_resource_type",
)

# Champs sans lesquels une ressource gamifiée n'a pas de sens : ils doivent être
# présents et non vides, sinon la sortie du Bridge est considérée inexploitable.
_BRIDGE_REQUIRED = ("behavioural_objective", "recommended_game_element")

_BRIDGE_MAX_TRIES = 2   # appel initial + 1 retry (re-prompt strict)


def _parse_bridge(raw: str) -> dict:
    """Extrait l'objet JSON de la réponse du LLM et vérifie les champs requis."""
    raw = raw.strip()
    start, end = raw.find("{"), raw.rfind("}") + 1
    if start == -1 or end <= start:
        raise ValueError("aucun objet JSON dans la réponse")
    parsed = json.loads(raw[start:end])
    manquants = [f for f in _BRIDGE_REQUIRED if not parsed.get(f)]
    if manquants:
        raise ValueError("champs requis manquants : " + ", ".join(manquants))
    return parsed


def node_bridge(state: AgentState) -> AgentState:
    """
    Bridge LLM : structure la sortie d'Agent 2 en champs pour Agent 3.

    En cas d'échec (LLM injoignable, ou sortie inexploitable après retry), on
    signale un échec EXPLICITE (status="bridge_failed") au lieu d'inventer des
    valeurs : la chaîne s'arrête et la raison remonte à l'utilisateur.
    """
    user_msg = (
        f"Leçon : {state.get('lesson', 'inconnue')}\n"
        f"Question : {state.get('user_input', '')}\n\n"
        f"{state.get('ontology_facts') or 'Aucun fait d ontologie.'}\n\n"
        "Choisis de préférence un élément de jeu et un objectif présents dans ces faits."
    )
    messages = [
        {"role": "system", "content": _BRIDGE_SYSTEM},
        {"role": "user", "content": user_msg},
    ]

    bridge, derniere_erreur = None, None
    for tentative in range(1, _BRIDGE_MAX_TRIES + 1):
        try:
            bridge = _parse_bridge(call_llm(messages))
            break
        except Exception as e:
            derniere_erreur = e
            print(f"[Bridge] tentative {tentative} invalide ({e})")
            messages.append({
                "role": "user",
                "content": "Ta réponse n'était pas un JSON valide et complet. "
                           "Renvoie UNIQUEMENT l'objet JSON avec les 5 champs.",
            })

    # Échec explicite : pas de valeurs fabriquées, on arrête la chaîne.
    if bridge is None:
        state["status"] = "bridge_failed"
        state["final_answer"] = (
            "Recommandation impossible : le service LLM n'a pas produit de sortie "
            f"exploitable ({derniere_erreur}). Aucune ressource n'est générée."
        )
        print("[Bridge] échec → abandon explicite")
        return state

    for field in _BRIDGE_FIELDS:
        state[field] = bridge.get(field)
    state["bridge_attempts"] = tentative
    state["status"] = "ok"
    print(f"[Bridge] élément de jeu = {state['recommended_game_element']} | "
          f"objectif = {state['behavioural_objective']}")
    return state


def route_after_bridge(state: AgentState) -> str:
    """Abandonne si le Bridge a échoué ; sinon continue vers la génération (Agent 3)."""
    return "abort" if state.get("status") == "bridge_failed" else "generate"


# =============================================================================
# Nœud 4 — Génération de ressource (Agent 3)
# =============================================================================

def node_generate_resource(state: AgentState) -> AgentState:
    """Agent 3 : génère la ressource gamifiée via son sous-graphe LangGraph."""
    print("[Agent 3] Génération de la ressource gamifiée...")
    from .agent3 import build_agent3_graph
    agent3_graph = build_agent3_graph()
    result = agent3_graph.invoke(state)
    state["generated_resource"] = result.get("generated_resource", "")
    state["resource_diagram"] = result.get("resource_diagram", "")   # version visuelle Mermaid
    state["final_answer"] = state["generated_resource"]
    return state
