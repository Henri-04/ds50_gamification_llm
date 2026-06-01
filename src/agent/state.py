#Définition des états de l'agent
from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict, total=False):
    # --- Champs existants (agent decide/tool/final) ---
    user_input: str
    decision: Optional[str]
    tool_result: Optional[str]
    final_answer: Optional[str]

    # --- Champs Agent 1 (résumé ontologie) ---

    # --- Champs Agent 2 (Agent de recommandation : NLP -> SPARQL -> execute) ---
    # Resume brut produit par l'Agent 1 (blob opaque, interprete par le LLM).
    ontology_summary: Optional[str]
    # Derniere requete SPARQL generee par le LLM.
    sparql_query: Optional[str]
    # Resultats reels renvoyes par l'ontologie (liste de lignes).
    query_results: Optional[List[Dict[str, Any]]]
    # Nombre de tentatives effectuees (boucle de retry).
    attempts: Optional[int]
    # Recommandation finale formatee a partir des donnees reelles.
    recommendation: Optional[str]

    # --- Champs Agent 3 (Agent de génération de ressources gamifiées) ---
    teacher: Optional[str]
    course: Optional[str]
    lesson: Optional[str]
    learner_profile: Optional[str]
    pedagogical_objective: Optional[str]
    behavioural_objective: Optional[str]
    recommended_game_element: Optional[str]
    recommended_resource_type: Optional[str]
    generated_resource: Optional[str]
