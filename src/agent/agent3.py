"""
Agent 3 — génération de la ressource gamifiée (provider NVIDIA).

Lit le state enrichi par Agent 1 → Agent 2 → Bridge, construit un prompt et
demande au LLM NVIDIA de produire une ressource pédagogique directement
utilisable par l'enseignant. N'effectue PAS de recommandation (déjà faite par
l'Agent 2) : il met en forme et concrétise.
"""

import os
import time
from datetime import datetime
from textwrap import dedent
from typing import Optional

from langgraph.graph import END, StateGraph

from .state import AgentState
from ..llm.nvidia_client import get_llm


# ============================================================
# Node LangGraph : génération de ressource
# ============================================================

def generate_resource(state: AgentState) -> AgentState:
    """
    Node principal de l'Agent 3.

    Lit le state, construit un prompt, appelle le LLM NVIDIA, puis place la
    ressource générée dans state["generated_resource"].
    """
    print("Agent 3 : préparation du prompt...")

    prompt = dedent(f"""
        Tu es l'Agent 3 d'un système d'aide à la gamification pédagogique.

        Ton rôle :
        Générer une ressource gamifiée personnalisée pour un enseignant.

        Attention :
        - Tu ne dois PAS faire la recommandation (déjà faite par un agent précédent).
        - Appuie-toi STRICTEMENT sur les FAITS DE L'ONTOLOGIE ci-dessous : réutilise
          les ressources, éléments de jeu et objectifs RÉELS qui y sont listés, et
          n'invente AUCUN fait sur l'ontologie.
        - Si une info manque, tu peux compléter pédagogiquement, sans contredire ces faits.

        {state.get("ontology_facts") or "(Aucun fait d'ontologie disponible.)"}

        Contexte enseignant :
        - Enseignant : {state.get("teacher", "inconnu")}
        - Cours : {state.get("course", "inconnu")}
        - Leçon : {state.get("lesson", "inconnue")}

        Profil apprenant :
        {state.get("learner_profile", "non précisé")}

        Objectifs :
        - Objectif pédagogique : {state.get("pedagogical_objective", "non précisé")}
        - Objectif comportemental / motivationnel : {state.get("behavioural_objective", "non précisé")}

        Élément de jeu recommandé : {state.get("recommended_game_element", "non précisé")}

        Génère une ressource directement utilisable par l'enseignant.

        Format attendu :

        # Titre

        ## Type de ressource

        ## Objectif pédagogique

        ## Objectif comportemental

        ## Élément de jeu utilisé

        ## Activité proposée

        ### Étape 1
        ### Étape 2
        ### Étape 3

        ## Feedback donné à l'apprenant

        ## Utilisation par l'enseignant

        ## Justification

        Réponds en français, de manière claire et concrète.
    """)

    print("Agent 3 : appel du modèle NVIDIA...")
    start = time.perf_counter()
    response = get_llm().invoke(prompt)
    print(f"Agent 3 : génération terminée en {time.perf_counter() - start:.2f} s")

    texte = response.content
    # Si l'Agent 2 n'a rien trouvé, la ressource n'est PAS basée sur l'ontologie.
    if not state.get("ontology_facts") and not state.get("query_results"):
        texte = ("> ⚠️ Ressource NON basée sur l'ontologie "
                 "(l'Agent 2 n'a trouvé aucune donnée pour cette demande).\n\n") + texte

    state["generated_resource"] = texte
    return state


# ============================================================
# Traçabilité (partagée backend .md <-> interface)
# ============================================================

def build_traceability(state: AgentState) -> str:
    """Section « Traçabilité » en Markdown : comment la reco a été obtenue.

    Source UNIQUE utilisée à la fois par le rapport .md (save_resource_to_file)
    et par l'interface (expander « Détails du raisonnement »), afin que le détail
    affiché soit strictement identique à la traçabilité des rapports backend.
    """
    sparql = state.get("sparql_query") or "(aucune)"
    facts = state.get("ontology_facts") or "(aucun)"
    blocks = [
        "## Traçabilité",
        f"**Question:** {state.get('user_input', '')}",
        "**Requête SPARQL générée par l'Agent 2 (= ce qu'il a décidé de chercher):**",
        f"```sparql\n{sparql}\n```",
        f"**Données trouvées dans l'ontologie:** {state.get('query_results')}",
        "**Faits riches récupérés (déterministe) :**",
        f"```\n{facts}\n```",
        f"**Recommandation Agent 2:** {state.get('recommendation', '')}",
        f"**Décision du Bridge:** élément de jeu = {state.get('recommended_game_element')}, "
        f"objectif = {state.get('behavioural_objective')}",
    ]
    return "\n\n".join(blocks)


# ============================================================
# Sauvegarde du résultat dans un fichier
# ============================================================

def save_resource_to_file(state: AgentState, filename: Optional[str] = None) -> str:
    """Sauvegarde la ressource générée dans outputs_agent3/ et retourne le chemin."""
    output_dir = "outputs_agent3"
    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resource_{timestamp}.md"

    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Ressource générée par Agent 3\n\n")
        f.write(f"**Enseignant:** {state.get('teacher', '?')}\n")
        f.write(f"**Cours:** {state.get('course', '?')}\n")
        f.write(f"**Leçon:** {state.get('lesson', '?')}\n")
        f.write(f"**Élément de jeu:** {state.get('recommended_game_element', '?')}\n")
        f.write(f"**Date de génération:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Traçabilité : comment la recommandation a été obtenue (le "comment", pas juste le "quoi").
        # Même bloc que celui affiché dans l'interface (build_traceability).
        f.write("---\n\n")
        f.write(build_traceability(state))
        f.write("\n\n---\n\n")
        f.write(state.get("generated_resource", ""))

    return filepath


# ============================================================
# Construction du graph LangGraph (sous-graphe Agent 3)
# ============================================================

def build_agent3_graph():
    """Baseline minimale : generate_resource -> END."""
    workflow = StateGraph(AgentState)
    workflow.add_node("generate_resource", generate_resource)
    workflow.set_entry_point("generate_resource")
    workflow.add_edge("generate_resource", END)
    return workflow.compile()


# ============================================================
# Démo locale : python -m src.agent.agent3
# ============================================================

def _demo_state() -> AgentState:
    """State d'exemple (autonome) pour tester l'Agent 3 sans les agents amont."""
    return {
        "teacher": "Sara",
        "course": "Lesson1_JavaBasics",
        "lesson": "Java Constructors",
        "learner_profile": (
            "Apprenants débutants en programmation Java, "
            "profil Socializer, style de compréhension séquentiel."
        ),
        "pedagogical_objective": "Comprendre le rôle d'un constructeur dans une classe Java.",
        "behavioural_objective": "Motivation",
        "recommended_game_element": "Progress Bar",
        "recommended_resource_type": "Mini-exercice gamifié",
        "query_results": [
            {
                "source": "ontology",
                "gameElement": "Progress Bar",
                "relatedObjective": "Motivation",
            }
        ],
    }


def main() -> None:
    agent3 = build_agent3_graph()
    result = agent3.invoke(_demo_state())

    print("\n==============================")
    print("RESSOURCE GÉNÉRÉE PAR AGENT 3")
    print("==============================\n")
    print(result["generated_resource"])

    filepath = save_resource_to_file(result)
    print(f"\n✓ Fichier sauvegardé : {filepath}")


if __name__ == "__main__":
    main()
