from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Define agent types and their descriptions
AGENT_TYPES = [
    {
        "name": "gbi",
        "description": "Goal-based investment questions, including financial planning, goals, and asset allocation."
    },
    {
        "name": "rate",
        "description": "Questions about Rate.com, its documents, policies, or company information."
    },
    {
        "name": "stocks",
        "description": "Questions about stocks, stock prices, company financials, or investment advice."
    },
    {
        "name": "generic",
        "description": "General knowledge or questions that any assistant can answer."
    },
    {
        "name": "out_of_scope",
        "description": "Irrelevant or unsupported questions outside the assistant’s capability."
    }
]

VALID_ROUTES = {a["name"] for a in AGENT_TYPES}

# LLM-based classifier for routing
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

CLASSIFY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
        You are a router that classifies user queries into one or more of the following agent types based on the content:
        {agent_types}

        Respond ONLY with a comma-separated list of the agent type names that are most relevant to answering the query.
        Do not explain your answer. Example: "gbi,stocks"
    """),
    ("human", "{query}")
])


def classify_query(query):
    agent_types_str = ", ".join([f"{a['name']}: {a['description']}" for a in AGENT_TYPES])
    prompt = CLASSIFY_PROMPT.format_messages(agent_types=agent_types_str, query=query)
    response = llm(prompt)

    # Parse and sanitize the response
    raw_output = response.content.strip().lower()
    routes = [r.strip() for r in raw_output.split(",") if r.strip() in VALID_ROUTES]

    if not routes:
        return ["out_of_scope"]

    return routes
