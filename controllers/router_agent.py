from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from controllers.agent_controller import create_agent_executor
from controllers.rag_agent import answer_ratecom_question

# Define agent types and their descriptions
AGENT_TYPES = [
    {
        "name": "stock",
        "description": "Questions about stocks, stock prices, company financials, or investment advice."
    },
    {
        "name": "ratecom",
        "description": "Questions about Rate.com, its documents, policies, or company information."
    },
    # Add more agent types here as needed
]

# LLM-based classifier for routing
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

CLASSIFY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a router that classifies user queries into one of the following agent types: {agent_types}. Respond ONLY with the agent type name (e.g., 'stock', 'ratecom'). Do not explain your answer."),
    ("human", "{query}")
])

def classify_query(query):
    agent_types_str = ", ".join([f"{a['name']}: {a['description']}" for a in AGENT_TYPES])
    prompt = CLASSIFY_PROMPT.format_messages(agent_types=agent_types_str, query=query)
    response = llm(prompt)
    agent_type = response.content.strip().lower()
    return agent_type

# Main router function
def route_query(query):
    agent_type = classify_query(query)
    if agent_type == "stock":
        agent_executor = create_agent_executor()
        return agent_executor.invoke({"input": query})["output"]
    elif agent_type == "ratecom":
        return answer_ratecom_question(query)
    else:
        return f"Sorry, I couldn't determine the right agent for your query."
