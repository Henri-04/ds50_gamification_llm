"""Client Groq (LangChain), utilisé par l'Agent 2 et le Bridge.

Le modèle est instancié de façon PARESSEUSE (au premier appel) : importer ce
module n'exige donc ni le paquet langchain_groq ni une clé API. Cela permet
notamment à la branche « recommandation de personnes » (100 % SPARQL) de
tourner sans dépendance LLM.
"""

from ..config import GROQ_MODEL

_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        from langchain_groq import ChatGroq
        _llm = ChatGroq(model=GROQ_MODEL, temperature=0.2)  # clé GROQ_API_KEY lue dans .env
    return _llm


def call_llm(messages):
    """messages = liste [{'role': ..., 'content': ...}]. Renvoie le texte de la réponse."""
    return _get_llm().invoke(messages).content
