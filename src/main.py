from agent.graph import agent_app
from dotenv import load_dotenv
load_dotenv()

state = {
    "user_input": "Qu'est-ce que la gamification ?",
    "decision": None,
    "tool_result": None,
    "final_answer": None,
}

result = agent_app.invoke(state)
print(result["final_answer"])