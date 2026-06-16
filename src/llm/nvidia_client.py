"""Client NVIDIA, utilisé par l'Agent 3. Clé NVIDIA_API_KEY dans .env.

Instanciation PARESSEUSE (au premier appel) : importer ce module n'exige ni le
paquet langchain_nvidia_ai_endpoints ni une clé API.
"""

from ..config import NVIDIA_MODEL

_llm = None
_llm_diagram = None


def get_llm():
    global _llm
    if _llm is None:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        _llm = ChatNVIDIA(model=NVIDIA_MODEL, temperature=0.3, max_completion_tokens=2500)
    return _llm


def get_diagram_llm():
    """Client dédié au diagramme Mermaid.

    gpt-oss est un modèle à raisonnement : sur un texte de ressource long, le
    raisonnement consomme tout le budget de tokens et le contenu final revient
    vide. On lui alloue donc un budget plus large (et une température basse, la
    sortie étant structurée)."""
    global _llm_diagram
    if _llm_diagram is None:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        _llm_diagram = ChatNVIDIA(model=NVIDIA_MODEL, temperature=0.1, max_completion_tokens=6000)
    return _llm_diagram
