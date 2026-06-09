"""
Démo interactive de la pipeline complète.

On choisit un enseignant, puis une de ses leçons, puis on pose une question.
La pipeline Agent 1 → Agent 2 → Bridge → Agent 3 génère ensuite une ressource.

Lancement (depuis la racine du projet) :
  python -m src.agent.test_pipeline
"""

from .nodes import (
    node_classify_intent, route_intent, node_recommend_people,
    node_load_taxonomy, node_recommend, node_bridge, node_generate_resource,
)
from .agent3 import save_resource_to_file
from .state import AgentState
from ..tools.sparql_tools import run_sparql
from ..config import DEFAULT_TEACHER, DEFAULT_COURSE


def list_teachers():
    """Tous les enseignants de l'ontologie (les 15 individus de type tco:Teacher)."""
    rows = run_sparql("SELECT DISTINCT ?teacher WHERE { ?teacher a tco:Teacher } ORDER BY ?teacher")
    return [r["teacher"] for r in rows]


def teacher_course(teacher):
    """Cours de spécialisation de l'enseignant (tgc:specializedIn), ou défaut."""
    rows = run_sparql(f"SELECT ?course WHERE {{ tgc:{teacher} tgc:specializedIn ?course }}")
    return rows[0]["course"] if rows else DEFAULT_COURSE


def select_teacher():
    """Affiche les enseignants et retourne celui choisi."""
    teachers = list_teachers()
    print("\n=== Qui êtes-vous ? ===")
    for i, teacher in enumerate(teachers, 1):
        print(f"  {i}. {teacher}  ({teacher_course(teacher)})")
    while True:
        choix = input("\nChoisissez votre profil enseignant (numéro) : ").strip()
        if choix.isdigit() and 1 <= int(choix) <= len(teachers):
            return teachers[int(choix) - 1]
        print("  Entrée invalide, réessayez.")


def lessons_of(teacher):
    """Leçons de l'enseignant (liste de noms), réutilisable par le CLI et l'app.

    Une leçon de l'enseignant = soit une leçon qu'il a conçue (tgc:designLesson),
    soit une leçon d'un cours qu'il enseigne (tco:teaches -> cours -> tco:consists_of
    -> leçon). NB : tco:teaches relie l'enseignant à un COURS, pas à une leçon ;
    d'où le passage par consists_of. L'union couvre les 15 enseignants.
    """
    rows = run_sparql(f"""
        SELECT DISTINCT ?lesson WHERE {{
          {{ tgc:{teacher} tgc:designLesson ?lesson }}
          UNION
          {{ tgc:{teacher} tco:teaches ?course . ?course tco:consists_of ?lesson }}
        }} ORDER BY ?lesson
    """)
    return [r["lesson"] for r in rows]


def select_lesson(teacher):
    """Affiche les leçons de l'enseignant et retourne celle choisie."""
    lessons = lessons_of(teacher)
    print(f"\n=== Leçons de {teacher} ===")
    for i, lesson in enumerate(lessons, 1):
        print(f"  {i}. {lesson}")
    while True:
        choix = input("\nChoisissez une leçon (numéro) : ").strip()
        if choix.isdigit() and 1 <= int(choix) <= len(lessons):
            return lessons[int(choix) - 1]
        print("  Entrée invalide, réessayez.")


def run_pipeline_steps(teacher, course, lesson, question, log=None):
    """Exécute la chaîne EXACTE de la pipeline et retourne le résultat + les étapes.

    Source unique de vérité pour le routage et l'enchaînement des nœuds : le CLI
    (run_interactive) ET l'interface Streamlit (app.py) passent par ici, donc la
    chaîne de raisonnement et les résultats sont strictement identiques.

    `log` : callable(str) optionnel pour tracer les étapes en live (le CLI passe
    `print` ; l'app peut l'ignorer ou capturer). Retourne un dict décrivant la
    branche empruntée et la sortie finale.
    """
    log = log or (lambda *_: None)

    state: AgentState = {
        "user_input": question,
        "teacher": teacher,
        "course": course,
        "lesson": lesson,
    }

    # Routage d'intention (cf. graph.py) : « qui peut m'aider / me mentorer ? »
    # part vers la branche personnes (déterministe, sans Agent 1/2/3) ; sinon,
    # pipeline ressource Agent 1 → Agent 2 → Bridge → Agent 3.
    log("\n[Intention] Classification de la question...")
    state = node_classify_intent(state)

    if route_intent(state) == "people":
        log("[Branche PERSONNES] Recommandation d'enseignants (mentors / pairs)...")
        state = node_recommend_people(state)
        return {
            "branch": "people",
            "intent": state.get("intent"),
            "people_recommendations": state.get("people_recommendations"),
            "final_answer": state.get("final_answer", ""),
            "state": state,
        }

    log("\n[Agent 1] Chargement de la taxonomie (génération si absente)...")
    state = node_load_taxonomy(state)

    log("[Agent 2] Génération de la recommandation...")
    state = node_recommend(state)
    log(f"  SPARQL : {(state.get('sparql_query') or '').strip()}")
    log(f"  Résultats : {len(state.get('query_results') or [])} ligne(s)")

    log("[Bridge] Structuration pour Agent 3...")
    state = node_bridge(state)
    log(f"  Élément de jeu : {state.get('recommended_game_element')}")

    log("[Agent 3] Génération de la ressource gamifiée...")
    state = node_generate_resource(state)

    return {
        "branch": "resource",
        "intent": state.get("intent"),
        "sparql_query": (state.get("sparql_query") or "").strip(),
        "n_results": len(state.get("query_results") or []),
        "recommended_game_element": state.get("recommended_game_element"),
        "generated_resource": state.get("generated_resource", ""),
        "final_answer": state.get("generated_resource", ""),
        "state": state,
    }


def run_interactive():
    print("=" * 60)
    print("  PIPELINE : Agent 1 → Agent 2 → Bridge → Agent 3")
    print("=" * 60)

    teacher = select_teacher()
    course = teacher_course(teacher)
    lesson = select_lesson(teacher)
    question = input(f"\nVotre question sur la gamification de '{lesson}' :\n> ").strip()

    result = run_pipeline_steps(teacher, course, lesson, question, log=print)

    if result["branch"] == "people":
        print("\n" + "=" * 60)
        print("PERSONNES RECOMMANDÉES")
        print("=" * 60)
        print(result.get("final_answer") or "(vide)")
        return

    print("\n" + "=" * 60)
    print("RESSOURCE GÉNÉRÉE")
    print("=" * 60)
    print(result.get("generated_resource") or "(vide)")

    filepath = save_resource_to_file(result["state"])
    print(f"\n✓ Sauvegardé : {filepath}")


if __name__ == "__main__":
    run_interactive()
