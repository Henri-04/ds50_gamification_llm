"""
Détection d'intention par LLM (Groq).

Aiguille la pipeline entre deux usages :
  - "people"   : recommander des PERSONNES (mentors, collègues, pairs, quelqu'un
                 à qui s'adresser / qui peut aider) ;
  - "resource" : recommander/générer une RESSOURCE gamifiée (comportement par défaut).

Contrairement à un matching de mots-clés (fragile aux formulations), le LLM
classe la question quelle que soit la tournure. En cas d'échec (API indisponible,
réponse inattendue), on retombe sur "resource" — la branche par défaut.
"""

from ..llm.groq_client import call_llm

_SYSTEM = """\
Tu es un classifieur d'intention pour un assistant de gamification pédagogique.
Tu reçois la question d'un enseignant et tu dois la classer dans UNE catégorie :

- "people"   : l'enseignant cherche une PERSONNE — un collègue, un mentor, un pair,
               quelqu'un à qui s'adresser, qui peut l'aider ou l'accompagner.
               Exemples : « à qui je pourrais m'adresser ? », « tu me recommandes
               qui pour m'aider ? », « quel collègue plus expérimenté peut me
               mentorer ? », « avec qui échanger sur ce sujet ? ».
- "resource" : TOUT LE RESTE — gamifier une leçon, obtenir une ressource, une
               activité, un élément de jeu, des idées, un quiz, un badge, etc.

Réponds par UN SEUL mot, en minuscules : people ou resource. Rien d'autre."""


def detect_intent(user_input: str) -> str:
    """Classe la question en 'people' ou 'resource' via le LLM (repli : 'resource')."""
    question = (user_input or "").strip()
    if not question:
        return "resource"

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": question},
    ]
    try:
        answer = call_llm(messages).strip().lower()
    except Exception as e:
        print(f"Intent : LLM indisponible ({e}) — repli sur 'resource'")
        return "resource"

    token = answer.split()[0] if answer else ""
    return "people" if token.startswith("people") else "resource"
