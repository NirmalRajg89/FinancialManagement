from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from typing import Literal, TypedDict, Optional, Any

from controllers.agent_controller import create_agent_executor
from controllers.memory_agent import memory_agent
from controllers.router_agent import classify_query
from controllers.gbi_agent import GBI_RAG_agent
from controllers.rate_agent import Rate_RAG_agent

ROUTE_TYPES = ["gbi", "rate", "stocks", "generic", "out_of_scope"]

shared_memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    input_key="question",
    max_token_limit=2000  # Prevent memory from growing too large
)

class AgentState(TypedDict):
    question: str
    routes: list[str]
    current_route: str  # Track current route separately
    answer: str
    intermediate: dict[str, str]  # Store single answer per route
    memory: Optional[ConversationBufferMemory]

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

    state["memory"] = shared_memory  # Use shared memory instance

    if route == "gbi":
        result = GBI_RAG_agent(state["question"], memory=state["memory"])
    elif route == "rate":
        result = Rate_RAG_agent(state["question"], memory=state["memory"])
    elif route == "stocks":
        gbi_context = state["intermediate"].get("gbi", "")
        enriched_question = f"{gbi_context}\n\n{state['question']}" if gbi_context else state["question"]
        result = create_agent_executor(enriched_question, memory=state["memory"])
    elif route == "generic":
        result = {"result": "Thank you. The provided information has been noted."}
    else:  # out_of_scope
        if "memory" in state and state["memory"] is not None:
            result = memory_agent(state["question"], chat_history = state["memory"].load_memory_variables({}).get("chat_history", ""))
        else:
            result = {
                "result": "I'm here to assist with financial-investments-related questions only and this query seems to be out-of-scope."}

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
            answers.append(answer)

    final_answer = "\n\n".join(answers)

    # Use the pre-initialized shared memory
    global shared_memory
    try:
        shared_memory.chat_memory.add_user_message(state["question"])
        shared_memory.chat_memory.add_ai_message(final_answer)
    except Exception as e:
        print(f"Memory update error: {str(e)}")

    print(f"[Merge Node] Final answer:\n{final_answer}")
    return {"answer": final_answer}

# concise combined answers
# def merge_results(state: AgentState):
#     # Combine all answers
#     answers = []
#     for route in state["routes"]:
#         if answer := state["intermediate"].get(route):
#             answers.append(f"{route.upper()}:\n{answer}")
#
#     combined_answer = "\n\n".join(answers) if answers else "No information available"
#
#     # Create summarization prompt
#     summarize_prompt = ChatPromptTemplate.from_template("""
#     You are a financial assistant. Below are multiple responses about a user's query:
#
#     {combined_responses}
#
#     Please provide a concise, coherent summary that:
#     1. Answers the original question directly
#     2. Integrates all relevant information
#
#     Final Summary:
#     """)
#
#     # Get summary from LLM
#     llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")  # Configure your LLM
#     summarizer = summarize_prompt | llm
#
#     try:
#         llm_response = summarizer.invoke({"combined_responses": combined_answer})
#         # Extract just the content if needed
#         if hasattr(llm_response, 'content'):  # For ChatMessage objects
#             final_answer = llm_response.content
#         elif isinstance(llm_response, str):  # If already a string
#             final_answer = llm_response
#         else:  # Fallback
#             final_answer = str(llm_response)
#     except Exception as e:
#         print(f"Summarization failed: {e}")
#         final_answer = combined_answer
#
#         # Clean up any metadata strings that might be present
#     final_answer = final_answer.split('content=')[-1].split('additional_kwargs')[0].strip()
#     final_answer = final_answer.strip("'\"")  # Remove any surrounding quotes
#
#     print(f"[Merge Node] Clean final answer:\n{final_answer}")
#     return {"answer": final_answer}
#

# Simplified graph construction
graph = StateGraph(AgentState)

graph.add_node("router", route_node)
graph.add_node("agent", agent_node)  # Consolidated all agent nodes
graph.add_node("next_route", next_route)
graph.add_node("merge", merge_results)

graph.set_entry_point("router")

# From router to first agent node
graph.add_edge("router", "agent")

# From agent to next route decision
graph.add_edge("agent", "next_route")

# Conditional edges after processing each route
graph.add_conditional_edges(
    "next_route",
    should_continue,
    {route: "agent" for route in ROUTE_TYPES} | {"merge": "merge"}
)

graph.add_edge("merge", END)

app = graph.compile()

if __name__ == "__main__":
    print("Starting financial assistant. Type 'exit' to end the session.\n")

    while True:
        question = input("Ask a question: ")
        if question.lower() in ['exit', 'quit']:
            print("\nFinal conversation history:")
            # print_memory(memory)
            break

        result = app.invoke({
            "question": question,
            "routes": [],
            "current_route": None,
            "answer": "",
            "intermediate": {},
            "memory": shared_memory  # Reuse the same memory instance
        })

        print("\nFinal Response:\n", result["answer"])