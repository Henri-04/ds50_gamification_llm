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
    print(f"Intention détectée : {state['intent']}")
    return state


def route_intent(state: AgentState) -> str:
    """Aiguillage LangGraph : 'people' -> recommandation de profs, sinon ressource."""
    return "people" if state.get("intent") == "people" else "resource"


def node_recommend_people(state: AgentState) -> AgentState:
    """Recommande des enseignants (mentors / pairs) à partir de l'ontologie."""
    from .people import recommend_people  # déterministe, pas de dépendance LLM
    return recommend_people(state)


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

    return "\n".join(lignes)


def node_load_taxonomy(state: AgentState) -> AgentState:
    """Charge taxonomy_for_agent_2.json, ou lance Agent 1 pour le générer."""
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
    return state


# =============================================================================
# Nœud 2 — Recommandation (Agent 2)
# =============================================================================

def node_recommend(state: AgentState) -> AgentState:
    """Agent 2 : question NL → SPARQL → recommandation."""
    from .agent2 import recommend
    return recommend(state)


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

# Champs que le Bridge doit produire, avec des valeurs de repli sûres si le LLM
# renvoie un JSON invalide : ainsi l'Agent 3 dispose toujours de tous les champs.
_BRIDGE_FIELDS = (
    "learner_profile",
    "pedagogical_objective",
    "behavioural_objective",
    "recommended_game_element",
    "recommended_resource_type",
)


def _bridge_fallback(state: AgentState) -> dict:
    """Valeurs par défaut si le LLM du Bridge échoue (JSON illisible/incomplet)."""
    return {
        "learner_profile": "Profil apprenant non précisé",
        "pedagogical_objective": state.get("lesson") or "Objectif pédagogique de la leçon",
        "behavioural_objective": "Motivation",
        "recommended_game_element": "Quiz",
        "recommended_resource_type": "activité interactive",
    }


def node_bridge(state: AgentState) -> AgentState:
    """Bridge LLM : structure la sortie d'Agent 2 en champs pour Agent 3."""
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

    fallback = _bridge_fallback(state)
    try:
        raw = call_llm(messages).strip()
        start, end = raw.find("{"), raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("aucun objet JSON dans la réponse du Bridge")
        bridge = json.loads(raw[start:end])
    except Exception as e:
        print(f"Bridge : sortie LLM illisible ({e}) — repli sur valeurs par défaut")
        bridge = {}

    # Complète les champs manquants avec le repli (robustesse Agent 3).
    for field in _BRIDGE_FIELDS:
        state[field] = bridge.get(field) or fallback[field]
    return state


# =============================================================================
# Nœud 4 — Génération de ressource (Agent 3)
# =============================================================================

def node_generate_resource(state: AgentState) -> AgentState:
    """Agent 3 : génère la ressource gamifiée via son sous-graphe LangGraph."""
    agent3_graph = build_agent3_graph()
    result = agent3_graph.invoke(state)
    state["generated_resource"] = result.get("generated_resource", "")
    state["final_answer"] = state["generated_resource"]
    return state
