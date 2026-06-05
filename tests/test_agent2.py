"""Tests d'Agent 2 — parsing SPARQL, mise en forme, et boucle exécution (LLM mocké)."""

from conftest import make_groq_response
from src.agent import agent2


def test_extract_sparql_from_code_fence():
    text = "Voici :\n```sparql\nSELECT ?x WHERE { ?x a ?y }\n```"
    assert agent2._extract_sparql(text) == "SELECT ?x WHERE { ?x a ?y }"


def test_extract_sparql_from_keyword():
    text = "Bien sûr ! SELECT ?x WHERE { ?x a ?y }"
    assert agent2._extract_sparql(text).startswith("SELECT")


def test_format_recommendation_empty():
    msg = agent2._format_recommendation("q", [])
    assert "Aucune" in msg


def test_format_recommendation_with_rows():
    msg = agent2._format_recommendation("q", [{"title": "Quiz", "vide": None}])
    assert "Quiz" in msg
    assert "vide" not in msg  # les valeurs None sont filtrées


def test_generate_and_run_success_with_mocked_llm(monkeypatch):
    """LLM mocké renvoie un SPARQL valide → exécution réelle sur l'ontologie."""
    sparql = "SELECT ?lesson WHERE { tgc:Sara tgc:designLesson ?lesson }"
    monkeypatch.setattr(agent2, "call_llm", lambda messages: make_groq_response(sparql))

    result = agent2.generate_and_run("Quelles leçons ?", "résumé fictif")

    assert result["error"] is None
    assert result["attempts"] == 1
    assert result["query_results"]


def test_generate_and_run_retries_on_invalid(monkeypatch):
    """Première requête invalide, seconde valide → succès en 2 tentatives."""
    bad = "SELECT ?x WHERE { ceci casse }"
    good = "SELECT ?lesson WHERE { tgc:Sara tgc:designLesson ?lesson }"
    responses = iter([bad, good])
    monkeypatch.setattr(
        agent2, "call_llm",
        lambda messages: make_groq_response(next(responses)),
    )

    result = agent2.generate_and_run("Quelles leçons ?", "résumé fictif")

    assert result["error"] is None
    assert result["attempts"] == 2
    assert result["query_results"]
