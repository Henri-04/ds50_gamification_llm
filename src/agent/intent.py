"""
Détection d'intention (déterministe, sans LLM ni dépendance lourde).

Permet d'aiguiller la pipeline entre deux usages :
  - "people"   : recommander des PERSONNES (mentors, collègues au profil proche) ;
  - "resource" : recommander/générer une RESSOURCE gamifiée (comportement par défaut).

Volontairement basé sur des mots-clés : robuste, instantané, testable sans clé API.
"""

import unicodedata

# Mots-clés signalant une demande de recommandation de PERSONNES (profs).
_PEOPLE_KEYWORDS = (
    "mentor", "mentorat", "mentore",
    "collegue", "collegues",
    "binome",
    "quel prof", "quels profs", "autre prof", "autres profs", "d autres profs",
    "quel enseignant", "quels enseignants", "autre enseignant", "autres enseignants",
    "plus experimente", "plus expert", "plus experimentes",
    "profil similaire", "profils similaires", "profil proche",
    "qui peut m aider", "qui pourrait m aider", "m accompagner", "se former",
    "recommande un prof", "recommander un prof", "recommande moi quelqu un",
    "une personne", "quelqu un qui",
)


def _normalize(text: str) -> str:
    """Minuscule + suppression des accents et apostrophes (matching robuste)."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    for ch in "'’-":
        text = text.replace(ch, " ")
    return text


def detect_intent(user_input: str) -> str:
    """Renvoie 'people' si la question vise des personnes, sinon 'resource'."""
    norm = _normalize(user_input or "")
    return "people" if any(kw in norm for kw in _PEOPLE_KEYWORDS) else "resource"
