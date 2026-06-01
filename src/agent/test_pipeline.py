"""
test_pipeline.py — Test interactif de la pipeline complète.

Flux :
  1. Agent 1 se lance en tâche de fond si taxonomy_for_agent_2.json est absent.
  2. L'utilisateur choisit une leçon de Sara dans le terminal.
  3. L'utilisateur pose une question sur la gamification de cette leçon.
  4. Agent 2 → Bridge → Agent 3 s'enchaînent automatiquement.

Lancement (depuis la racine du projet) :
  .venv/bin/python src/agent/test_pipeline.py
"""

import sys
import threading
from pathlib import Path

_AGENT_DIR = Path(__file__).resolve().parent
_SRC_DIR = _AGENT_DIR.parent
_PROJECT_ROOT = _SRC_DIR.parent

for _p in (str(_AGENT_DIR), str(_SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tools.sparql_tools import run_sparql
from nodes import node_load_taxonomy, node_recommend, node_bridge, node_generate_resource
from agent3 import save_resource_to_file
from state import AgentState

TAXONOMY_PATH = _PROJECT_ROOT / "taxonomy_for_agent_2.json"


def _generate_taxonomy_in_background():
    """Lance Agent 1 en tâche de fond si le fichier de taxonomie est absent."""
    if TAXONOMY_PATH.exists():
        print(f"[Agent 1] Taxonomie existante : {TAXONOMY_PATH.name}")
        return None

    print("[Agent 1] taxonomy_for_agent_2.json absent → génération en tâche de fond...")

    def _run():
        state: AgentState = {}
        node_load_taxonomy(state)
        print(f"[Agent 1] ✓ Taxonomie générée")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


def select_lesson() -> str:
    """Affiche les leçons de Sara (SPARQL) et retourne celle choisie."""
    rows = run_sparql("""
        SELECT DISTINCT ?lesson WHERE {
          tgc:Sara tgc:designLesson ?lesson .
        }
        ORDER BY ?lesson
    """)
    lessons = [r["lesson"] for r in rows]

    print("\n=== Leçons de Sara ===")
    for i, lesson in enumerate(lessons, 1):
        resources = run_sparql(f"""
            SELECT ?title WHERE {{
              tgc:{lesson} tco:reuseResource ?res .
              OPTIONAL {{ ?res tgc:has_title ?title }}
            }}
        """)
        titles = [r["title"] for r in resources if r.get("title")]
        suffix = f"  → {', '.join(titles[:2])}" if titles else ""
        print(f"  {i}. {lesson}{suffix}")

    while True:
        choice = input("\nChoisissez une leçon (numéro) : ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(lessons):
            return lessons[int(choice) - 1]
        print("  Entrée invalide, réessayez.")


def run_pipeline():
    print("=" * 60)
    print("  TEST PIPELINE : Agent 1 → Agent 2 → Agent 3")
    print("=" * 60)

    # Agent 1 en tâche de fond si besoin
    agent1_thread = _generate_taxonomy_in_background()

    # Sélection leçon + question (pendant qu'Agent 1 tourne si besoin)
    lesson = select_lesson()
    question = input(f"\nVotre question sur la gamification de '{lesson}' :\n> ").strip()

    # Attendre Agent 1 si encore en cours
    if agent1_thread is not None:
        print("\n[Agent 1] En cours, veuillez patienter...")
        agent1_thread.join()

    # Construction du state initial
    state: AgentState = {
        "user_input": question,
        "teacher": "Sara",
        "course": "ObjectOrientedProgramming",
        "lesson": lesson,
    }

    # Charger la taxonomie dans le state
    print("\n[Agent 1] Chargement de la taxonomie...")
    state = node_load_taxonomy(state)

    # Agent 2
    print("[Agent 2] Génération de la recommandation...")
    state = node_recommend(state)
    print(f"  SPARQL : {(state.get('sparql_query') or '')[:80]}...")
    print(f"  Résultats : {len(state.get('query_results') or [])} ligne(s)")
    print(f"  Recommandation : {(state.get('recommendation') or '')[:150]}...")

    # Bridge
    print("\n[Bridge] Structuration pour Agent 3...")
    state = node_bridge(state)
    print(f"  Élément de jeu : {state.get('recommended_game_element')}")
    print(f"  Objectif comportemental : {state.get('behavioural_objective')}")

    # Agent 3
    print("\n[Agent 3] Génération de la ressource gamifiée...")
    state = node_generate_resource(state)

    print("\n" + "=" * 60)
    print("RESSOURCE GÉNÉRÉE")
    print("=" * 60)
    print(state.get("generated_resource", "(vide)"))

    filepath = save_resource_to_file(state)
    print(f"\n✓ Sauvegardé : {filepath}")


if __name__ == "__main__":
    run_pipeline()
