"""Pipeline LangGraph : Agent 1 → Agent 2 → Bridge → Agent 3."""
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import node_load_taxonomy, node_recommend, node_bridge, node_generate_resource
from ..config import DEFAULT_TEACHER, DEFAULT_COURSE


def create_pipeline():
    """Crée le graphe de la pipeline complète."""
    graph = StateGraph(AgentState)

    graph.add_node("load_taxonomy", node_load_taxonomy)
    graph.add_node("recommend", node_recommend)
    graph.add_node("bridge", node_bridge)
    graph.add_node("generate_resource", node_generate_resource)

    graph.set_entry_point("load_taxonomy")
    graph.add_edge("load_taxonomy", "recommend")
    graph.add_edge("recommend", "bridge")
    graph.add_edge("bridge", "generate_resource")
    graph.add_edge("generate_resource", END)

    return graph.compile()


def run_pipeline(
    user_input: str,
    teacher: str = DEFAULT_TEACHER,
    course: str = DEFAULT_COURSE,
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
