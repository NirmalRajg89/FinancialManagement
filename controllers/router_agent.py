from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Define agent types and their descriptions
AGENT_TYPES = [
    # {
    #     "name": "allocator",
    #     "description": "Lifecycle/Target Date Fund asset allocation questions."
    # },
    {
        "name": "gbi",
        "description": "Goal-based investment questions, including financial planning, goals, and Lifecycle/Target Date Fund asset allocation questions."
    },
    {
        "name": "rate",
        "description": "Questions about HELOC (Home Equity Line of Credit) and it's rates, reverse mortgage, HECM (Home Equity Conversion Mortgage), requirements for a credit score on a personal loan, and RateDocs its documents, policies, or company information."
    },
    {
        "name": "diversify",
        "description": "Question asking to diversify the investment"
    },
    {
        "name": "stocks",
        "description": "Questions about stocks, stock prices, company financials, or investment advice."
    },
    {
        "name": "generic",
        "description": "Information provided instead of asking a question."
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


def classify_query(query: str) -> list[str]:
    # Combine all agent descriptions into a single string
    agent_descriptions = ", ".join([
        f"{agent['name']}: {agent['description']}" for agent in AGENT_TYPES
    ])

    # Format the prompt using the agent types and user query
    prompt_messages = CLASSIFY_PROMPT.format_messages(
        agent_types=agent_descriptions,
        query=query
    )

    # Send prompt to the LLM
    response = llm(prompt_messages)

    # Parse the response: e.g., "gbi, stocks" → ["gbi", "stocks"]
    raw_routes = response.content.split(",")
    routes = [route.strip().lower() for route in raw_routes]

    # Filter only valid agent names
    valid_agent_names = [agent["name"] for agent in AGENT_TYPES]
    filtered_routes = [route for route in routes if route in valid_agent_names]

    return filtered_routes

