from typing import TypedDict, Optional

class AgentState(TypedDict):
    """État enrichi pour orchestration LangGraph robuste et traçable."""

    # Contexte de conversation (multi-tour)
    conversation_history: list[dict]
    current_query: str

    # Schéma & règles de base
    ontology_schema: str
    ontology_rules: list[dict]
    rag_results: list[dict]

    # Chaîne de raisonnement (traçabilité complète)
    reasoning_chain: list[str]
    required_queries: list[str]
    query_results: dict

    # Recommandation en cours
    draft_recommendation: str
    validation_errors: list[str]
    is_valid: bool
    retry_count: int

    # Résultat final
    final_answer: str
    confidence: str
    needs_clarification: bool
