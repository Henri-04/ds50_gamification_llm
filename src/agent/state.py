from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict, total=False):
    # Entrée utilisateur
    user_input: str
    final_answer: str
    intent: Optional[str]   # "people" (recommander des profs) ou "resource" (défaut)

    # Contexte enseignant (fourni par l'appelant ou l'interactif)
    teacher: Optional[str]
    course: Optional[str]
    lesson: Optional[str]

    # Agent 2 — NL → SPARQL → résultats
    ontology_summary: Optional[str]
    sparql_query: Optional[str]
    query_results: Optional[List[Dict[str, Any]]]
    attempts: Optional[int]
    recommendation: Optional[str]
    ontology_facts: Optional[str]   # faits riches récupérés sur la leçon (déterministe)

    # Bridge LLM → champs structurés pour Agent 3
    learner_profile: Optional[str]
    pedagogical_objective: Optional[str]
    behavioural_objective: Optional[str]
    recommended_game_element: Optional[str]
    recommended_resource_type: Optional[str]

    # Agent 3 — ressource gamifiée générée
    generated_resource: Optional[str]

    # Recommandation de personnes (mentors / pairs)
    people_recommendations: Optional[Dict[str, Any]]
