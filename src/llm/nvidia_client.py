"""Client NVIDIA, utilisé par l'Agent 3. Clé NVIDIA_API_KEY dans .env.

Instanciation PARESSEUSE (au premier appel) : importer ce module n'exige ni le
paquet langchain_nvidia_ai_endpoints ni une clé API.
"""

from ..config import NVIDIA_MODEL

_llm = None


def get_llm():
    global _llm
    if _llm is None:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        _llm = ChatNVIDIA(model=NVIDIA_MODEL, temperature=0.3, max_completion_tokens=2500)
    return _llm
