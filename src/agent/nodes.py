"""
Nœuds de la pipeline Agent 1 → Agent 2 → Bridge → Agent 3.

Chaque nœud prend un AgentState et retourne un AgentState enrichi.
"""

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]   # .../src/
_AGENT = Path(__file__).resolve().parent      # .../src/agent/
for _p in (str(_AGENT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from llm.groq_client import call_llm
from agent2 import recommend
from agent3 import build_agent3_graph
from state import AgentState

TAXONOMY_PATH = Path(__file__).resolve().parents[2] / "taxonomy_for_agent_2.json"


# =============================================================================
# Nœud 1 — Taxonomie (Agent 1)
# =============================================================================

def node_load_taxonomy(state: AgentState) -> AgentState:
    """Charge taxonomy_for_agent_2.json, ou lance Agent 1 pour le générer."""
    if TAXONOMY_PATH.exists():
        with open(TAXONOMY_PATH, encoding="utf-8") as f:
            taxonomy = json.load(f)
    else:
        print("[Agent 1] Fichier absent — génération...")
        from agent1 import extract_structure, curate_with_llm, apply_filter, fallback_keep
        structure = extract_structure()
        try:
            keep = curate_with_llm(structure)
        except Exception as e:
            print(f"[Agent 1] ⚠ LLM indisponible ({e}) — repli déterministe")
            keep = fallback_keep(structure)
        taxonomy = apply_filter(structure, keep)
        with open(TAXONOMY_PATH, "w", encoding="utf-8") as f:
            json.dump(taxonomy, f, indent=2, ensure_ascii=False)

    state["ontology_summary"] = json.dumps(taxonomy, ensure_ascii=False, separators=(",", ":"))
    return state


# =============================================================================
# Nœud 2 — Recommandation (Agent 2)
# =============================================================================

def node_recommend(state: AgentState) -> AgentState:
    """Agent 2 : question NL → SPARQL → recommandation."""
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


def node_bridge(state: AgentState) -> AgentState:
    """Bridge LLM : structure la sortie d'Agent 2 en champs pour Agent 3."""
    user_msg = (
        f"Leçon : {state.get('lesson', 'inconnue')}\n"
        f"Question : {state.get('user_input', '')}\n"
        f"Recommandation Agent 2 : {state.get('recommendation', '')}\n"
        f"Données SPARQL (extrait) : {json.dumps((state.get('query_results') or [])[:5], ensure_ascii=False)}"
    )
    messages = [
        {"role": "system", "content": _BRIDGE_SYSTEM},
        {"role": "user", "content": user_msg},
    ]
    response = call_llm(messages)
    raw = response.choices[0].message.content.strip()
    start, end = raw.find("{"), raw.rfind("}") + 1
    bridge = json.loads(raw[start:end])
    state.update(bridge)
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
