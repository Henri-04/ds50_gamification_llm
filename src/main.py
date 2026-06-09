"""
Point d'entrée CLI de GamiTeach.

Flux interactif :
  1. Choix de l'enseignant (parmi les 15 de l'ontologie).
  2. Choix d'un de ses cours.
  3. Choix d'une de ses leçons dans ce cours.
  4. Question → pipeline (graph.run_pipeline) → réponse → sauvegarde fichier.

Lancement (depuis la racine du projet) :
    python -m src.main
"""

from .pipeline import list_teachers, courses_of, lessons_of, run
from .agent.agent3 import save_resource_to_file


def _choisir(options: list[str], invite: str) -> str:
    """Affiche une liste numérotée et renvoie l'option choisie."""
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        choix = input(invite).strip()
        if choix.isdigit() and 1 <= int(choix) <= len(options):
            return options[int(choix) - 1]
        print("  Entrée invalide, réessayez.")


def main() -> None:
    print("=" * 60)
    print("  GamiTeach — Assistant de gamification pédagogique")
    print("=" * 60)

    # 1. Enseignant
    print("\n=== Qui êtes-vous ? ===")
    teacher = _choisir(list_teachers(), "\nChoisissez votre profil enseignant (numéro) : ")

    # 2. Cours
    courses = courses_of(teacher)
    if not courses:
        print(f"\n{teacher} n'a conçu aucune leçon dans l'ontologie — rien à gamifier.")
        return
    print(f"\n=== Cours de {teacher} ===")
    course = _choisir(courses, "\nChoisissez un cours (numéro) : ")

    # 3. Leçon
    print(f"\n=== Leçons de {teacher} dans {course} ===")
    lesson = _choisir(lessons_of(teacher, course), "\nChoisissez une leçon (numéro) : ")

    # 4. Question → pipeline
    question = input(f"\nVotre question sur la gamification de '{lesson}' :\n> ").strip()

    print("\n" + "-" * 60)
    print("  Pipeline en cours...")
    print("-" * 60)
    state = run(question, teacher, course, lesson)

    # Affichage selon l'intention détectée
    if state.get("intent") == "people":
        print("\n" + "=" * 60)
        print("PERSONNES RECOMMANDÉES")
        print("=" * 60)
        print(state.get("final_answer") or "(vide)")
        return

    print("\n" + "=" * 60)
    print("RESSOURCE GÉNÉRÉE")
    print("=" * 60)
    print(state.get("generated_resource") or state.get("final_answer") or "(vide)")

    filepath = save_resource_to_file(state)
    print(f"\n✓ Sauvegardé : {filepath}")


if __name__ == "__main__":
    main()