#Gestion des noeuds du graphe 

from llm.groq_client import call_llm
from tools.neo4j_tools import query_ontology
from tools.rag_tools import search_course_content
from .state import AgentState


def decide_action(state: AgentState) -> AgentState:
    prompt = f"""
    Tu dois décider quelle source utiliser :
    - "ontology" si la question est conceptuelle
    - "course" si elle concerne le contenu du cours

    Question : {state["user_input"]}
    Réponds uniquement par un mot.
    """

    response = call_llm([{"role": "user", "content": prompt}])
    decision = response.choices[0].message.content.strip().lower()

    state["decision"] = decision
    return state


def use_tool(state: AgentState) -> AgentState:
    if state["decision"] == "ontology":
        state["tool_result"] = query_ontology(state["user_input"])
    else:
        state["tool_result"] = search_course_content(state["user_input"])

    return state


def finalize(state: AgentState) -> AgentState:
    state["final_answer"] = state["tool_result"]
    return state