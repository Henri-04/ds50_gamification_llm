"""Tests de l'exécution SPARQL (aucune clé API requise)."""

import pytest

from src.tools.sparql_tools import run_sparql, get_graph


def test_graph_loads():
    g = get_graph()
    assert len(g) > 0


def test_prefixes_are_injected_automatically():
    # La requête n'a pas de PREFIX : ils doivent être injectés automatiquement.
    rows = run_sparql("SELECT ?lesson WHERE { tgc:Sara tgc:designLesson ?lesson }")
    assert isinstance(rows, list)
    assert rows, "Sara devrait concevoir des leçons dans l'ontologie"
    assert "lesson" in rows[0]


def test_iris_are_shortened():
    rows = run_sparql("SELECT ?lesson WHERE { tgc:Sara tgc:designLesson ?lesson }")
    # _shorten ne garde que le nom local (pas d'URI http complète).
    assert all("http" not in r["lesson"] for r in rows)


def test_invalid_query_raises():
    with pytest.raises(Exception):
        run_sparql("SELECT ?x WHERE { ceci n'est pas du SPARQL }")
