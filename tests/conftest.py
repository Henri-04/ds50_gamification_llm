"""Utilitaires partagés par les tests."""


def make_groq_response(content: str):
    """call_llm renvoie directement le texte de la réponse : le mock renvoie donc une string."""
    return content
