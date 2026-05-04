#Graph d'orchestration LangGraph 

from langgraph.graph import StateGraph, END
from .nodes import decide_action, use_tool, finalize
from .state import AgentState

graph = StateGraph(AgentState)

graph.add_node("decide", decide_action)
graph.add_node("tool", use_tool)
graph.add_node("final", finalize)

graph.set_entry_point("decide")
graph.add_edge("decide", "tool")
graph.add_edge("tool", "final")
graph.add_edge("final", END)

agent_app = graph.compile()

