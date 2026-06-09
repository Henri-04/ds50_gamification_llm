"""
Pipeline LangGraph avec routage d'intention :

                         ┌─ (people)   → recommend_people → END
  classify_intent ──────┤
                         └─ (resource) → load_taxonomy → recommend → bridge
                                         → generate_resource → END
"""
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    node_classify_intent, route_intent, node_recommend_people,
    node_load_taxonomy, node_recommend, node_bridge, node_generate_resource,
    route_after_recommend, route_after_bridge,
)


def create_pipeline():
    """Crée le graphe de la pipeline complète (ressource OU personnes)."""
    graph = StateGraph(AgentState)

    graph.add_node("classify_intent", node_classify_intent)
    graph.add_node("recommend_people", node_recommend_people)
    graph.add_node("load_taxonomy", node_load_taxonomy)
    graph.add_node("recommend", node_recommend)
    graph.add_node("bridge", node_bridge)
    graph.add_node("generate_resource", node_generate_resource)

    graph.set_entry_point("classify_intent")
    graph.add_conditional_edges(
        "classify_intent", route_intent,
        {"people": "recommend_people", "resource": "load_taxonomy"},
    )
    # Branche « personnes » : déterministe, pas d'Agent 1/2/3.
    graph.add_edge("recommend_people", END)
    # Branche « ressource » : pipeline historique, avec abandon explicite si
    # aucun fait n'est exploitable (Agent 2) ou si le Bridge échoue.
    graph.add_edge("load_taxonomy", "recommend")
    graph.add_conditional_edges(
        "recommend", route_after_recommend,
        {"abort": END, "bridge": "bridge"},
    )
    graph.add_conditional_edges(
        "bridge", route_after_bridge,
        {"abort": END, "generate": "generate_resource"},
    )
    graph.add_edge("generate_resource", END)

    return graph.compile()


def run_pipeline(
    user_input: str,
    teacher: str = "",
    course: str = "",
    lesson: str = "",
) -> dict:
    """Lance la pipeline complète et retourne le state final."""
    pipeline = create_pipeline()
    initial_state: AgentState = {
        "user_input": user_input,
        "teacher": teacher,
        "course": course,
        "lesson": lesson,
    }
    return pipeline.invoke(initial_state)
