"""Client NVIDIA, utilisé par l'Agent 3. Clé NVIDIA_API_KEY dans .env."""

from langchain_nvidia_ai_endpoints import ChatNVIDIA

from ..config import NVIDIA_MODEL

llm = ChatNVIDIA(model=NVIDIA_MODEL, temperature=0.3, max_completion_tokens=2500)
