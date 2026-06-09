"""Configuration du projet : clés API (.env) et réglages simples."""

from dotenv import load_dotenv

load_dotenv()  # charge GROQ_API_KEY et NVIDIA_API_KEY depuis le fichier .env

# Modèles LLM
GROQ_MODEL = "llama-3.3-70b-versatile"        # Agent 2 + Bridge
GROQ_CURATION_MODEL = "openai/gpt-oss-120b"   # Agent 1 (curation de l'ontologie)
NVIDIA_MODEL = "openai/gpt-oss-120b"          # Agent 3
