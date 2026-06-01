"""Graphe d'orchestration LangGraph robuste avec 7 nœuds."""
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    analyze_query,
    fetch_ontology_rules,
    fetch_rag_content,
    generate_draft,
    validate_recommendation,
    refine_or_clarify,
    format_with_citations,
)


def create_agent_graph():
    """Crée le graphe LangGraph avec orchestration robuste."""
    graph = StateGraph(AgentState)

    # Ajouter les 7 nœuds
    graph.add_node("analyze_query", analyze_query)
    graph.add_node("fetch_ontology_rules", fetch_ontology_rules)
    graph.add_node("fetch_rag_content", fetch_rag_content)
    graph.add_node("generate_draft", generate_draft)
    graph.add_node("validate_recommendation", validate_recommendation)
    graph.add_node("refine_or_clarify", refine_or_clarify)
    graph.add_node("format_with_citations", format_with_citations)

    # Flux linéaire
    graph.set_entry_point("analyze_query")
    graph.add_edge("analyze_query", "fetch_ontology_rules")
    graph.add_edge("fetch_ontology_rules", "fetch_rag_content")
    graph.add_edge("fetch_rag_content", "generate_draft")
    graph.add_edge("generate_draft", "validate_recommendation")
    graph.add_edge("validate_recommendation", "refine_or_clarify")

    # Boucle conditionnelle
    def conditional_route(state: AgentState) -> str:
        if state.get("is_valid"):
            return "format_with_citations"
        elif state.get("needs_clarification"):
            return "format_with_citations"
        elif state.get("retry_count", 0) < 2:
            return "validate_recommendation"
        else:
            return "format_with_citations"

    graph.add_conditional_edges(
        "refine_or_clarify",
        conditional_route,
        {
            "format_with_citations": "format_with_citations",
            "validate_recommendation": "validate_recommendation",
        },
    )

    graph.add_edge("format_with_citations", END)
    return graph.compile()


agent_app = create_agent_graph()


def run_agent(user_query: str, conversation_history: list[dict] = None) -> dict:
    """Lance l'agent avec une question utilisateur."""
    if conversation_history is None:
        conversation_history = []

    initial_state = AgentState(
        conversation_history=conversation_history,
        current_query=user_query,
        ontology_schema="",
        ontology_rules=[],
        rag_results=[],
        reasoning_chain=[],
        required_queries=[],
        query_results={},
        draft_recommendation="",
        validation_errors=[],
        is_valid=False,
        retry_count=0,
        final_answer="",
        confidence="medium",
        needs_clarification=False,
    )

    result = agent_app.invoke(initial_state)

    return {
        "final_answer": result.get("final_answer", ""),
        "confidence": result.get("confidence", "unknown"),
        "reasoning_chain": result.get("reasoning_chain", []),
        "is_valid": result.get("is_valid", False),
        "needs_clarification": result.get("needs_clarification", False),
        "ontology_rules_used": len(result.get("ontology_rules", [])),
        "rag_passages_used": len(result.get("rag_results", [])),
    }
