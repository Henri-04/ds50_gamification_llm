"""
Baseline simple de l'Agent 3.

Ce fichier regroupe volontairement :
- le State LangGraph
- les mock inputs des agents précédents
- le node generate_resource
- la construction du graph
- le main de test

But : avoir une baseline facile à comprendre avant de séparer le code
plus proprement en plusieurs fichiers si le projet grossit.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph
import time

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from llm.nvidia_client import llm
from state import AgentState


# ============================================================
# 1. Mock temporaire des agents précédents
# ============================================================

def mock_previous_agents_output() -> AgentState:
    """
    Simule les sorties des agents précédents.

    À remplacer plus tard par le vrai state venant de :
    - Agent 1 : résumé / contexte ontologique
    - Agent 2 : recommandation + résultats de requête
    """

    return {
        "user_input": "",
        "decision": None,
        "tool_result": None,
        "final_answer": None,
        "teacher": "Sara",
        "course": "Lesson1_JavaBasics",
        "lesson": "Java Constructors",

        "learner_profile": (
            "Apprenants débutants en programmation Java, "
            "profil Socializer, style de compréhension séquentiel."
        ),

        "pedagogical_objective": (
            "Comprendre le rôle d’un constructeur dans une classe Java."
        ),

        "behavioural_objective": "Motivation",
        "recommended_game_element": "Progress Bar",
        "recommended_resource_type": "Mini-exercice gamifié",

        "query_results": [
            {
                "source": "ontology",
                "gameElement": "Progress Bar",
                "relatedObjective": "Motivation",
                "explanation": (
                    "La barre de progression permet de visualiser l’avancement "
                    "de l’apprenant et de renforcer sa motivation."
                ),
            },
            {
                "source": "ontology",
                "lesson": "Java Constructors",
                "topic": "Object Oriented Programming",
                "course": "Lesson1_JavaBasics",
            },
            {
                "source": "recommendation_agent",
                "recommendation": (
                    "Utiliser une barre de progression pour guider les étudiants "
                    "dans une activité étape par étape sur les constructeurs Java."
                ),
            },
        ],

        "generated_resource": None,
    }



# ============================================================
# 3. Node LangGraph : génération de ressource
# ============================================================

def generate_resource(state: AgentState) -> AgentState:
    """
    Node principal de l'Agent 3.

    Il lit le state, construit un prompt, appelle le LLM,
    puis ajoute la ressource générée dans state["generated_resource"].
    """

    print("  → Node generate_resource démarré")
    print("  → Préparation du prompt...")


    prompt = dedent(f"""
        Tu es l'Agent 3 d'un système d'aide à la gamification pédagogique.

        Ton rôle :
        Générer une ressource gamifiée personnalisée pour un enseignant.

        Attention :
        - Tu ne dois PAS faire la recommandation.
        - La recommandation a déjà été faite par un agent précédent.
        - Tu dois utiliser l'élément de jeu recommandé.
        - Tu dois t'appuyer sur les données reçues.
        - Si certaines informations sont incomplètes, tu peux proposer une version pédagogique cohérente,
            mais sans inventer de faux faits sur l'ontologie.

        Contexte enseignant :
        - Enseignant : {state["teacher"]}
        - Cours : {state["course"]}
        - Leçon : {state["lesson"]}

        Profil apprenant :
        {state["learner_profile"]}

        Objectifs :
        - Objectif pédagogique : {state["pedagogical_objective"]}
        - Objectif comportemental / motivationnel : {state["behavioural_objective"]}

        Recommandation reçue :
        - Élément de jeu recommandé : {state["recommended_game_element"]}
        - Type de ressource recommandé : {state["recommended_resource_type"]}

        Résultats fournis par les agents précédents :
        {state["query_results"]}

        Génère une ressource directement utilisable par l'enseignante.

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

        ## Utilisation par l'enseignante

        ## Justification

        Réponds en français, de manière claire et concrète.
    """)

    print("  → Appel du modèle NVIDIA en cours...")
    start = time.perf_counter()
    
    response = llm.invoke(prompt)

    end = time.perf_counter()
    print(f"  → Appel du modèle terminé en {end - start:.2f} secondes.")

    state["generated_resource"] = response.content

    print("  → State mis à jour avec generated_resource")

    return state


# ============================================================
# 4. Sauvegarde du résultat dans un fichier
# ============================================================

def save_resource_to_file(state: AgentState, filename: Optional[str] = None) -> str:
    """
    Sauvegarde la ressource générée dans un fichier.

    Args:
        state : le state contenant la ressource générée
        filename : nom du fichier optionnel (sinon auto-généré avec timestamp)

    Returns:
        Le chemin du fichier créé
    """

    # Créer le répertoire output s'il n'existe pas
    output_dir = "outputs_agent3"
    os.makedirs(output_dir, exist_ok=True)

    # Générer le nom du fichier avec timestamp si nécessaire
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resource_{timestamp}.md"

    filepath = os.path.join(output_dir, filename)

    # Écrire la ressource dans le fichier
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Ressource générée par Agent 3\n\n")
        f.write(f"**Enseignant:** {state['teacher']}\n")
        f.write(f"**Cours:** {state['course']}\n")
        f.write(f"**Leçon:** {state['lesson']}\n")
        f.write(f"**Élément de jeu:** {state['recommended_game_element']}\n")
        f.write(f"**Date de génération:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write(state["generated_resource"])

    return filepath


# ============================================================
# 5. Construction du graph LangGraph
# ============================================================

def build_agent3_graph():
    """
    Baseline minimale :
    generate_resource -> END
    """

    workflow = StateGraph(AgentState)

    workflow.add_node("generate_resource", generate_resource)
    workflow.set_entry_point("generate_resource")
    workflow.add_edge("generate_resource", END)

    return workflow.compile()


# ============================================================
# 6. Test local de l'Agent 3
# ============================================================

def main() -> None:
    """
    Lance l'Agent 3 avec les données mockées.
    """

    print("[1/4] Construction du graphe...")
    agent3 = build_agent3_graph()
    
    print("[2/4] Chargement des données mock...")
    initial_state = mock_previous_agents_output()

    print("[3/4] Lancement de l'Agent 3...")
    start = time.perf_counter()

    result = agent3.invoke(initial_state)

    end = time.perf_counter()
    print(f"[4/4] Génération terminée en {end - start:.2f} secondes.")

    print("\n==============================")
    print("RESSOURCE GÉNÉRÉE PAR AGENT 3")
    print("==============================\n")
    print(result["generated_resource"])

    # Sauvegarde dans un fichier
    print("\n==============================")
    filepath = save_resource_to_file(result)
    print(f"✓ Fichier sauvegardé : {filepath}")
    print("==============================")


if __name__ == "__main__":
    main()
