"""Tests du Bridge (nodes.node_bridge) — échec EXPLICITE, jamais de fabrication (LLM mocké)."""

from conftest import make_groq_response
from src.agent import nodes

_VALID = (
    '{"learner_profile":"P","pedagogical_objective":"O",'
    '"behavioural_objective":"Motivation","recommended_game_element":"Quiz",'
    '"recommended_resource_type":"activité interactive"}'
)


def test_bridge_parses_valid_json(monkeypatch):
    monkeypatch.setattr(nodes, "call_llm", lambda messages: make_groq_response(_VALID))

    out = nodes.node_bridge({"user_input": "q", "lesson": "L"})

    assert out["status"] == "ok"
    assert out["recommended_game_element"] == "Quiz"
    assert out["behavioural_objective"] == "Motivation"


def test_bridge_fails_explicitly_on_garbage(monkeypatch):
    """Sortie non-JSON : échec explicite, aucun champ fabriqué."""
    monkeypatch.setattr(
        nodes, "call_llm",
        lambda messages: make_groq_response("désolé, pas de JSON ici"),
    )

    out = nodes.node_bridge({"user_input": "q", "lesson": "Java"})

    assert out["status"] == "bridge_failed"
    assert out.get("recommended_game_element") is None       # rien d'inventé
    assert "impossible" in out["final_answer"].lower()


def test_bridge_fails_explicitly_when_llm_raises(monkeypatch):
    """LLM injoignable (ex: clé API manquante) : échec explicite, pas de repli."""
    def boom(messages):
        raise RuntimeError("clé API manquante")
    monkeypatch.setattr(nodes, "call_llm", boom)

    out = nodes.node_bridge({"lesson": "Réseaux"})

    assert out["status"] == "bridge_failed"
    assert out.get("behavioural_objective") is None


def test_bridge_fails_on_partial_json(monkeypatch):
    """JSON valide mais champ requis manquant : échec explicite (pas de comblement)."""
    monkeypatch.setattr(
        nodes, "call_llm",
        lambda messages: make_groq_response('{"recommended_game_element":"Badge"}'),
    )

    out = nodes.node_bridge({"lesson": "L"})

    assert out["status"] == "bridge_failed"       # behavioural_objective manquant
    assert out.get("learner_profile") is None     # aucun champ Agent 3 fabriqué


def test_bridge_retries_then_succeeds(monkeypatch):
    """1re réponse invalide → retry → 2e réponse valide acceptée."""
    reponses = iter(["pas de json", _VALID])
    monkeypatch.setattr(
        nodes, "call_llm",
        lambda messages: make_groq_response(next(reponses)),
    )

    out = nodes.node_bridge({"lesson": "L"})

    assert out["status"] == "ok"
    assert out["recommended_game_element"] == "Quiz"
