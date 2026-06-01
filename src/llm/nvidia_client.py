import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

llm = ChatNVIDIA(
    model=os.getenv("NVIDIA_MODEL", "openai/gpt-oss-120b"),
    temperature=0.3,
    max_completion_tokens=2500,
)