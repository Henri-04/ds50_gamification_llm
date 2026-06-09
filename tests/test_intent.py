"""Tests de la détection d'intention (classification LLM Groq).

Les cas sémantiques appellent réellement le LLM → nécessitent GROQ_API_KEY
(skippés sinon). Les cas vide/None restent purs (court-circuit sans appel LLM).
"""

import os

import pytest

from src.agent.intent import detect_intent  # import -> config.load_dotenv() (.env chargé)

_needs_api = pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY requis (détection par LLM)"
)


@_needs_api
@pytest.mark.parametrize("question", [
    "Quel collègue plus expérimenté pourrait me mentorer ?",
    "Quels profs ont un profil similaire au mien ?",
    "Je cherche un mentor en gamification",
    "À qui je pourrais m'adresser pour gamifier ma leçon ?",   # ratait en mots-clés
    "Tu me recommandes qui pour m'aider ?",                    # ratait en mots-clés
    "Avec qui échanger sur ce sujet ?",
])
def test_detects_people_intent(question):
    assert detect_intent(question) == "people"


@_needs_api
@pytest.mark.parametrize("question", [
    "Comment gamifier ma leçon sur l'héritage ?",
    "Quelle ressource pour motiver mes élèves ?",
    "Propose une activité avec des badges",
    "Recommande-moi une ressource qui aide à gamifier",        # piège : 'qui' relatif
])
def test_detects_resource_intent(question):
    assert detect_intent(question) == "resource"


def test_empty_and_none_default_to_resource():
    # Court-circuit sans appel LLM : robustesse garantie même hors-ligne.
    assert detect_intent("") == "resource"
    assert detect_intent(None) == "resource"
