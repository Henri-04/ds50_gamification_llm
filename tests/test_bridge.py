"""Tests du Bridge (nodes.node_bridge) — parsing JSON et repli robuste (LLM mocké)."""

from conftest import make_groq_response
from src.agent import nodes


def test_bridge_parses_valid_json(monkeypatch):
    payload = (
        '{"learner_profile":"P","pedagogical_objective":"O",'
        '"behavioural_objective":"Motivation","recommended_game_element":"Quiz",'
        '"recommended_resource_type":"activité interactive"}'
    )
    monkeypatch.setattr(nodes, "call_llm", lambda messages: make_groq_response(payload))

    out = nodes.node_bridge({"user_input": "q", "lesson": "L"})

    assert out["recommended_game_element"] == "Quiz"
    assert out["behavioural_objective"] == "Motivation"


def test_bridge_falls_back_on_garbage_output(monkeypatch):
    monkeypatch.setattr(
        nodes, "call_llm",
        lambda messages: make_groq_response("désolé, pas de JSON ici"),
    )

    out = nodes.node_bridge({"user_input": "q", "lesson": "Java"})

    # Tous les champs requis par Agent 3 sont présents grâce au repli.
    for field in nodes._BRIDGE_FIELDS:
        assert out.get(field)
    assert out["pedagogical_objective"] == "Java"  # le repli réutilise la leçon


def test_bridge_falls_back_when_llm_raises(monkeypatch):
    def boom(messages):
        raise RuntimeError("clé API manquante")

    monkeypatch.setattr(nodes, "call_llm", boom)

    out = nodes.node_bridge({"lesson": "Réseaux"})

    for field in nodes._BRIDGE_FIELDS:
        assert out.get(field)


def test_bridge_completes_partial_json(monkeypatch):
    """JSON valide mais incomplet → champs manquants comblés par le repli."""
    monkeypatch.setattr(
        nodes, "call_llm",
        lambda messages: make_groq_response('{"recommended_game_element":"Badge"}'),
    )

    out = nodes.node_bridge({"lesson": "L"})

    assert out["recommended_game_element"] == "Badge"  # valeur du LLM conservée
    assert out["learner_profile"]  # champ manquant comblé
