#Définition des états de l'agent
from typing import TypedDict, Optional

class AgentState(TypedDict):
    user_input: str
    decision: Optional[str]
    tool_result: Optional[str]
    final_answer: Optional[str]