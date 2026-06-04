"""Client Groq (LangChain), utilisé par l'Agent 2 et le Bridge."""

from langchain_groq import ChatGroq

from ..config import GROQ_MODEL

llm = ChatGroq(model=GROQ_MODEL, temperature=0.2)  # clé GROQ_API_KEY lue dans .env


def call_llm(messages):
    """messages = liste [{'role': ..., 'content': ...}]. Renvoie le texte de la réponse."""
    return llm.invoke(messages).content
