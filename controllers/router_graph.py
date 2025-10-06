# router_graph.py
import streamlit as st
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

from controllers.agent_controller import create_agent_executor
from controllers.memory_agent import memory_agent
from controllers.portfolio_optimizer_agent import portfolio_optimizer_agent
from controllers.router_agent import classify_query
from controllers.gbi_agent import GBI_RAG_agent
from controllers.rate_agent import Rate_RAG_agent
from controllers.send_media_agent import send_media_agent

ROUTE_TYPES = ["gbi", "rate", "diversify", "media", "stocks", "generic", "out_of_scope"]

class AgentState(TypedDict):
    question: str
    routes: list[str]
    current_route: str
    answer: str
    intermediate: dict[str, str]
    memory: Optional[ConversationSummaryBufferMemory]
    session_id: str

def route_node(state: AgentState) -> dict:
    routes = classify_query(state["question"])
    if not routes:
        routes = ["out_of_scope"]
    print(f"[Router] Routes determined: {routes}")
    return {
        "routes": routes,
        "current_route": routes[0] if routes else None,
        "intermediate": {},
    }

def agent_node(state: AgentState):
    route = state["current_route"]
    print(f"[{route.capitalize()} Node] Processing")
    # print(str(state["memory"].load_memory_variables({})))
    # print(str(state))
    if route == "gbi":
        result = GBI_RAG_agent(state["question"], memory=state["memory"])
    elif route == "rate":
        result = Rate_RAG_agent(state["question"], memory=state["memory"])
    elif route == "diversify":
        result = portfolio_optimizer_agent(st.session_state.static_vars )
    elif route == "media":
        result = send_media_agent(st.session_state.get("chat_history", []))
    elif route == "stocks":
        gbi_context = state["intermediate"].get("gbi", "")
        enriched_question = f"{gbi_context}\n\n{state['question']}" if gbi_context else state["question"]
        agent_executor = create_agent_executor(enriched_question, memory=state["memory"])
        result = agent_executor.ask(enriched_question)  # This will give you the actual output

    elif route == "generic":
        result = {"result": "Thank you. The provided information has been noted."}
    else:  # out_of_scope
        if "memory" in state and state["memory"] is not None:
            result = memory_agent(
                state["question"],
                chat_history=state["memory"].load_memory_variables({}).get("chat_history", "")
            )
        else:
            print("out memory")
            result = {
                "result": "I'm here to assist with financial-investments-related questions only and this query seems to be out-of-scope."
            }

    state["intermediate"][route] = result if route == "stocks" else result["result"]
    return {}

def next_route(state: AgentState):
    current_idx = state["routes"].index(state["current_route"])
    if current_idx + 1 < len(state["routes"]):
        return {"current_route": state["routes"][current_idx + 1]}
    return {"current_route": None}

def should_continue(state: AgentState):
    return state["current_route"] if state["current_route"] else "merge"

def merge_results(state: AgentState):
    answers = []
    for route in state["routes"]:
        if answer := state["intermediate"].get(route):
            # Ensure answer is a string, if it's not, handle it appropriately
            if isinstance(answer, dict) and "result" in answer:
                answers.append(answer["result"])
            elif isinstance(answer, str):
                answers.append(answer)
            else:
                # Handle other unexpected types, possibly by logging or handling gracefully
                answers.append(str(answer))

    final_answer = "\n\n".join(answers)

    # Update memory if it exists
    if state["memory"] is not None:
        try:
            state["memory"].chat_memory.add_user_message(state["question"])
            state["memory"].chat_memory.add_ai_message(final_answer)
        except Exception as e:
            print(f"Memory update error: {str(e)}")

    print(f"[Merge Node] Final answer:\n{final_answer}")
    return {"answer": final_answer}

# Graph construction
graph = StateGraph(AgentState)
graph.add_node("router", route_node)
graph.add_node("agent", agent_node)
graph.add_node("next_route", next_route)
graph.add_node("merge", merge_results)

graph.set_entry_point("router")
graph.add_edge("router", "agent")
graph.add_edge("agent", "next_route")

graph.add_conditional_edges(
    "next_route",
    should_continue,
    {route: "agent" for route in ROUTE_TYPES} | {"merge": "merge"}
)

graph.add_edge("merge", END)

app = graph.compile()