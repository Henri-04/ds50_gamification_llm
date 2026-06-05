"""
Point d'entrée CLI de la pipeline de gamification.

Lance Agent 1 → Agent 2 → Bridge → Agent 3 sur une question, et affiche la
ressource gamifiée générée.

Usage (depuis la racine du projet) :
    python -m src.main "Comment gamifier ma leçon sur l'héritage ?"
    python -m src.main                 # question de démonstration par défaut
"""

import sys

from .agent.graph import run_pipeline
from .config import DEFAULT_TEACHER, DEFAULT_COURSE

_DEMO_QUESTION = "Comment motiver les élèves avec la gamification ?"


def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    question = " ".join(argv).strip() or _DEMO_QUESTION

    print("=" * 70)
    print(f"Question : {question}")
    print(f"Enseignant : {DEFAULT_TEACHER} | Cours : {DEFAULT_COURSE}")
    print("=" * 70)

    result = run_pipeline(question)

    print("\n" + "=" * 70)
    print("RESSOURCE GÉNÉRÉE")
    print("=" * 70)
    print(result.get("final_answer") or result.get("generated_resource") or "(vide)")


if __name__ == "__main__":
    main()
