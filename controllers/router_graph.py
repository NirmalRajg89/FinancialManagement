from langchain.memory import ConversationBufferMemory
from langgraph.graph import StateGraph, END
from typing import Literal, TypedDict, Optional, Any

from controllers.agent_controller import create_agent_executor
from controllers.router_agent import classify_query
from controllers.gbi_agent import GBI_RAG_agent
from controllers.rate_agent import Rate_RAG_agent

ROUTE_TYPES = ["gbi", "rate", "stocks", "generic", "out_of_scope"]

class AgentState(TypedDict):
    question: str
    route: Literal["gbi", "rate", "stocks", "generic", "out_of_scope"]
    answer: str
    memory: Optional[Any]  # Allow storing memory object


def route_node(state: AgentState):
    route = classify_query(state["question"])
    if route not in ROUTE_TYPES:
        route = "out_of_scope"
    print(f'[Router] Question: {state["question"]}\nClassified Route: {route}')
    return {"route": route}

def gbi_node(state: AgentState):
    response = GBI_RAG_agent(state["question"])
    return {"answer": response["result"]}

def rate_node(state: AgentState):
    response = Rate_RAG_agent(state["question"])
    return {"answer": response["result"]}

def stocks_node(state: AgentState):
    return {"answer": create_agent_executor(state["question"])}

def generic_node(state: AgentState):
    return {"answer": "I'm here to assist with financial-investments-related questions. This appears to be a general inquiry, which falls outside the scope of my expertise."}

def oos_node(state: AgentState):
    return {"answer": "This question is out of scope. Please try a different question."}

# Construct the graph
graph = StateGraph(AgentState)

graph.add_node("router", route_node)
graph.add_node("gbi", gbi_node)
graph.add_node("rate", rate_node)
graph.add_node("stocks", stocks_node)
graph.add_node("generic", generic_node)
graph.add_node("out_of_scope", oos_node)

# Set the entry point
graph.set_entry_point("router")

# Route to specific agent based on decision
graph.add_conditional_edges(
    "router",
    lambda state: state["route"],
    path_map={
        "gbi": "gbi",
        "rate": "rate",
        "stocks": "stocks",
        "generic": "generic",
        "out_of_scope": "out_of_scope",
    },
)

# Final output from each node
for leaf in ["gbi", "rate", "stocks", "generic", "out_of_scope"]:
    graph.add_edge(leaf, END)

# Compile the graph
app = graph.compile()

if __name__ == "__main__":
    question = input("Ask a question: ")
    result = app.invoke({
        "question": question,
        "memory": ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    })
    print("\nAgent route:", result["route"])
    print("Response:", result["answer"])
