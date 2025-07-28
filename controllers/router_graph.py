from langchain.memory import ConversationBufferMemory
from langgraph.graph import StateGraph, END
from typing import Literal, TypedDict, Optional, Any, List

from controllers.agent_controller import create_agent_executor
from controllers.router_agent import classify_query
from controllers.gbi_agent import GBI_RAG_agent
from controllers.rate_agent import Rate_RAG_agent

ROUTE_TYPES = ["gbi", "rate", "stocks", "generic", "out_of_scope"]

class AgentState(TypedDict):
    question: str
    route: List[Literal["gbi", "rate", "stocks", "generic", "out_of_scope"]]
    answer: str
    memory: Optional[Any]  # Allow storing memory object

def route_node(state: AgentState):
    routes = classify_query(state["question"])
    valid_routes = [r for r in routes if r in ROUTE_TYPES]
    if not valid_routes:
        valid_routes = ["out_of_scope"]
    print(f"[Router] Question: {state['question']}\nClassified Routes: {valid_routes}")
    return {"route": valid_routes}

def gbi_node(state: AgentState):
    response = GBI_RAG_agent(state["question"])
    return f"🏠 *Goal-Based Advice*: {response['result']}"

def rate_node(state: AgentState):
    response = Rate_RAG_agent(state["question"])
    return f"💰 *Interest Rate Insight*: {response['result']}"

def stocks_node(state: AgentState):
    response = create_agent_executor(state["question"])
    return f"📈 *Stock Suggestion*: {response}"

def generic_node(state: AgentState):
    return "📘 I'm focused on financial topics. This seems general."

def oos_node(state: AgentState):
    return "🚫 The question is out of scope."

def multi_agent_node(state: AgentState):
    routes = state["route"]
    responses = []

    for route in routes:
        if route == "gbi":
            responses.append(gbi_node(state))
        elif route == "rate":
            responses.append(rate_node(state))
        elif route == "stocks":
            responses.append(stocks_node(state))
        elif route == "generic":
            responses.append(generic_node(state))
        elif route == "out_of_scope":
            responses.append(oos_node(state))

    return {"answer": "\n\n".join(responses)}

# Construct the graph
graph = StateGraph(AgentState)

graph.add_node("router", route_node)
graph.add_node("multi", multi_agent_node)

# Set the entry point
graph.set_entry_point("router")

# Route all from router to multi node
graph.add_edge("router", "multi")
graph.add_edge("multi", END)

# Compile the graph
app = graph.compile()

if __name__ == "__main__":
    question = input("Ask a question: ")
    result = app.invoke({
        "question": question,
        "memory": ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    })
    print("\nAgent routes:", result["route"])
    print("Response:\n", result["answer"])
