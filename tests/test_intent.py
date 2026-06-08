"""Tests de la détection d'intention (déterministe, aucune dépendance LLM)."""

import pytest

from src.agent.intent import detect_intent


@pytest.mark.parametrize("question", [
    "Quel collègue plus expérimenté pourrait me mentorer ?",
    "Quels profs ont un profil similaire au mien ?",
    "Je cherche un mentor en gamification",
    "Y a-t-il un autre enseignant qui pourrait m'aider ?",
    "MENTOR disponible ?",                       # robustesse à la casse
    "Peux-tu me recommander un prof plus expert ?",
])
def test_detects_people_intent(question):
    assert detect_intent(question) == "people"


@pytest.mark.parametrize("question", [
    "Comment gamifier ma leçon sur l'héritage ?",
    "Quelle ressource pour motiver mes élèves ?",
    "Propose une activité avec des badges",
    "",
])
def test_defaults_to_resource_intent(question):
    assert detect_intent(question) == "resource"


def test_none_input_is_resource():
    assert detect_intent(None) == "resource"
