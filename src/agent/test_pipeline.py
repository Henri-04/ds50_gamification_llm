"""
test_pipeline.py — Test de la pipeline complète Agent 1 → Agent 2 → Agent 3.

Flux :
  1. Agent 1 se lance en tâche de fond si taxonomy_for_agent_2.json est absent.
  2. L'utilisateur choisit une leçon de Sara dans le terminal.
  3. L'utilisateur pose une question sur la gamification de cette leçon.
  4. Agent 2 traduit la question en SPARQL et l'exécute sur l'ontologie.
  5. Un appel LLM "bridge" formate la sortie d'Agent 2 pour Agent 3.
  6. Agent 3 génère la ressource gamifiée et la sauvegarde.

Lancement (depuis la racine du projet) :
  .venv/bin/python src/agent/test_pipeline.py
"""

import json
import sys
import threading
from pathlib import Path

# --- Chemins -----------------------------------------------------------------
_AGENT_DIR = Path(__file__).resolve().parent   # .../src/agent/
_SRC_DIR = _AGENT_DIR.parent                   # .../src/
_PROJECT_ROOT = _SRC_DIR.parent                # racine du projet

for _p in (str(_AGENT_DIR), str(_SRC_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# --- Imports -----------------------------------------------------------------
from tools.sparql_tools import run_sparql
from llm.groq_client import call_llm
from state import AgentState
from agent2_recommender import recommend
from agent3 import build_agent3_graph, save_resource_to_file

TAXONOMY_PATH = _PROJECT_ROOT / "taxonomy_for_agent_2.json"


# =============================================================================
# ÉTAPE 1 — Agent 1 : chargement ou génération de la taxonomie
# =============================================================================

def _run_agent1():
    """Exécute le pipeline Agent 1 et écrit taxonomy_for_agent_2.json."""
    from agent_1 import (
        extract_structure, build_filter_input,
        curate_with_llm, apply_filter, fallback_keep,
    )
    print("[Agent 1] Phase 1 — extraction déterministe...")
    structure = extract_structure()
    print(f"[Agent 1] Phase 2 — curation LLM...")
    try:
        keep = curate_with_llm(structure)
    except Exception as e:
        print(f"[Agent 1] ⚠ LLM indisponible ({e}) — repli déterministe")
        keep = fallback_keep(structure)
    print("[Agent 1] Phase 3 — reconstruction + intégrité...")
    result = apply_filter(structure, keep)
    with open(TAXONOMY_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[Agent 1] ✓ Taxonomie générée : {TAXONOMY_PATH.name} "
          f"({len(result['classes'])} classes, {len(result['object_properties'])} propriétés)")


def load_taxonomy() -> tuple[dict | None, threading.Thread | None]:
    """
    Si le fichier existe → le charge et retourne (taxonomy, None).
    Sinon → lance Agent 1 en tâche de fond et retourne (None, thread).
    """
    if TAXONOMY_PATH.exists():
        print(f"[Agent 1] Taxonomie existante : {TAXONOMY_PATH.name}")
        with open(TAXONOMY_PATH, encoding="utf-8") as f:
            return json.load(f), None

    print("[Agent 1] taxonomy_for_agent_2.json absent → génération en tâche de fond...")
    t = threading.Thread(target=_run_agent1, daemon=True)
    t.start()
    return None, t


# =============================================================================
# ÉTAPE 2 — Sélection interactive (Teacher : Sara)
# =============================================================================

def select_lesson() -> str:
    """Affiche les leçons de Sara et retourne celle choisie par l'utilisateur."""
    rows = run_sparql("""
        SELECT DISTINCT ?lesson WHERE {
          tgc:Sara tgc:designLesson ?lesson .
        }
        ORDER BY ?lesson
    """)
    lessons = [r["lesson"] for r in rows]

    print("\n=== Leçons de Sara ===")
    for i, lesson in enumerate(lessons, 1):
        # Ressources existantes (aperçu)
        resources = run_sparql(f"""
            SELECT ?title WHERE {{
              tgc:{lesson} tco:reuseResource ?res .
              OPTIONAL {{ ?res tgc:has_title ?title }}
            }}
        """)
        titles = [r.get("title") or "" for r in resources if r.get("title")]
        suffix = f"  → {', '.join(titles[:2])}" if titles else ""
        print(f"  {i}. {lesson}{suffix}")

    while True:
        choice = input("\nChoisissez une leçon (numéro) : ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(lessons):
            return lessons[int(choice) - 1]
        print("  Entrée invalide, réessayez.")


# =============================================================================
# ÉTAPE 4 — Bridge LLM : Agent 2 → Agent 3
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


def bridge_to_agent3(question: str, lesson: str, recommendation: str, query_results: list) -> dict:
    """Petit appel LLM (llama-3.1-8b) pour structurer la sortie Agent 2 en entrée Agent 3."""
    user_msg = (
        f"Leçon : {lesson}\n"
        f"Question : {question}\n"
        f"Recommandation Agent 2 : {recommendation}\n"
        f"Données SPARQL (extrait) : {json.dumps(query_results[:5], ensure_ascii=False)}"
    )
    messages = [
        {"role": "system", "content": _BRIDGE_SYSTEM},
        {"role": "user", "content": user_msg},
    ]
    response = call_llm(messages)
    raw = response.choices[0].message.content.strip()
    start, end = raw.find("{"), raw.rfind("}") + 1
    return json.loads(raw[start:end])


# =============================================================================
# PIPELINE PRINCIPALE
# =============================================================================

def run_pipeline():
    print("=" * 60)
    print("  TEST PIPELINE : Agent 1 → Agent 2 → Agent 3")
    print("=" * 60)

    # Étape 1 — Taxonomie
    taxonomy, agent1_thread = load_taxonomy()

    # Étape 2 — Sélection leçon + question (pendant qu'Agent 1 tourne si besoin)
    lesson = select_lesson()
    question = input(f"\nVotre question sur la gamification de '{lesson}' :\n> ").strip()

    # Attendre Agent 1 si encore en cours
    if agent1_thread is not None:
        print("\n[Agent 1] En cours, veuillez patienter...")
        agent1_thread.join()
        with open(TAXONOMY_PATH, encoding="utf-8") as f:
            taxonomy = json.load(f)

    # Sérialisation en string (format attendu par Agent 2)
    ontology_summary = json.dumps(taxonomy, ensure_ascii=False, separators=(",", ":"))

    # Étape 3 — Agent 2
    print("\n[Agent 2] Génération de la recommandation...")
    state: AgentState = {
        "user_input": question,
        "ontology_summary": ontology_summary,
    }
    state = recommend(state)
    print(f"  SPARQL : {(state.get('sparql_query') or '')[:80]}...")
    print(f"  Résultats : {len(state.get('query_results') or [])} ligne(s)")
    print(f"  Recommandation : {(state.get('recommendation') or '')[:150]}...")

    # Étape 4 — Bridge Agent 2 → Agent 3
    print("\n[Bridge] Structuration pour Agent 3...")
    bridge = bridge_to_agent3(
        question=question,
        lesson=lesson,
        recommendation=state.get("recommendation", ""),
        query_results=state.get("query_results") or [],
    )
    print(f"  Élément de jeu : {bridge.get('recommended_game_element')}")
    print(f"  Objectif comportemental : {bridge.get('behavioural_objective')}")

    # Mise à jour du state avec les champs Agent 3
    state.update({
        "teacher": "Sara",
        "course": "ObjectOrientedProgramming",
        "lesson": lesson,
        **bridge,
    })

    # Étape 5 — Agent 3
    print("\n[Agent 3] Génération de la ressource gamifiée...")
    agent3_graph = build_agent3_graph()
    result = agent3_graph.invoke(state)

    print("\n" + "=" * 60)
    print("RESSOURCE GÉNÉRÉE")
    print("=" * 60)
    print(result.get("generated_resource", "(vide)"))

    filepath = save_resource_to_file(result)
    print(f"\n✓ Sauvegardé : {filepath}")


if __name__ == "__main__":
    run_pipeline()
