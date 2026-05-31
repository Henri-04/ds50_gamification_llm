#Définition des états de l'agent
from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    user_input: str
    decision: Optional[str]
    tool_result: Optional[str]
    final_answer: Optional[str]

    # --- Champs Agent 1 (résumé ontologie) ---

    # --- Champs Agent 2 (Agent de recommandation : NLP -> SPARQL -> execute) ---

    # --- Champs Agent 3 (Agent de génération de ressources gamifiées) ---
    teacher: Optional[str]
    course: Optional[str]
    lesson: Optional[str]
    learner_profile: Optional[str]
    pedagogical_objective: Optional[str]
    behavioural_objective: Optional[str]
    recommended_game_element: Optional[str]
    recommended_resource_type: Optional[str]
    query_results: Optional[List[Dict[str, Any]]]
    generated_resource: Optional[str]