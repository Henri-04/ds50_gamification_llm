"""
src/pipeline.py — Logique partagée entre le CLI (main.py) et l'interface (app.py).

Deux responsabilités, et deux seulement :
  - Helpers de sélection (SPARQL) : enseignants → cours → leçons.
  - run() : point d'entrée unique qui délègue à graph.run_pipeline (LangGraph).

L'orchestration des agents reste dans agent/graph.py (source unique de vérité) ;
ce module n'ajoute que les requêtes de sélection et l'enveloppe d'appel commune,
pour que CLI et interface produisent strictement les mêmes résultats.
"""

from .tools.sparql_tools import run_sparql
from .agent.graph import run_pipeline


# ── Sélection : enseignant → cours → leçon ────────────────────────────────────

def list_teachers() -> list[str]:
    """Les 15 enseignants de l'ontologie (individus de type tco:Teacher)."""
    rows = run_sparql("SELECT DISTINCT ?t WHERE { ?t a tco:Teacher } ORDER BY ?t")
    return [r["t"] for r in rows]


def courses_of(teacher: str) -> list[str]:
    """
    Cours contenant au moins une leçon conçue par cet enseignant.

    Lien indirect : teacher --designLesson--> leçon <--consists_of-- cours.
    (Certains enseignants « profil seul » ne conçoivent aucune leçon → liste vide.)
    """
    rows = run_sparql(f"""
        SELECT DISTINCT ?course WHERE {{
            ?course tco:consists_of ?lesson .
            tgc:{teacher} tgc:designLesson ?lesson .
        }} ORDER BY ?course
    """)
    return [r["course"] for r in rows]


def lessons_of(teacher: str, course: str) -> list[str]:
    """Leçons conçues par cet enseignant à l'intérieur de ce cours."""
    rows = run_sparql(f"""
        SELECT DISTINCT ?lesson WHERE {{
            tgc:{teacher} tgc:designLesson ?lesson .
            tgc:{course} tco:consists_of ?lesson .
        }} ORDER BY ?lesson
    """)
    return [r["lesson"] for r in rows]


# ── Exécution de la pipeline ──────────────────────────────────────────────────

def run(question: str, teacher: str, course: str, lesson: str) -> dict:
    """
    Point d'entrée unique : lance la pipeline LangGraph et renvoie le state final.

    Le state contient selon l'intention détectée :
      - branche ressource : generated_resource, final_answer, sparql_query, ...
      - branche personnes : people_recommendations, final_answer, intent == "people"
    """
    return run_pipeline(user_input=question, teacher=teacher, course=course, lesson=lesson)