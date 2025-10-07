from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor
from langchain.chat_models import ChatOpenAI

from models.portfolio_optimizer import portfolio_optimizer


def portfolio_optimizer_agent(static_vars: dict):
    """
    Agent that only executes portfolio_optimizer and returns results safely.
    static_vars should include:
        - monthly_contribution
        - tenure (months or years)
        - plan_type ('short_term' or 'long_term')
        - goal_amount
        - funds (dict of fund_name -> expected_return)
    """
    funds = {
        "Bank Savings Account": 0.035,
        "Recurring Deposit": 0.06,
        "Public Provident Fund": 0.075,
        "Equity Mutual Funds": 0.10,
        "Index Funds": 0.125,
        "Stock Market": 0.175
    }

    # --- 1. Sanitize numeric inputs ---
    plan_type = static_vars.get("plan_type", "long_term")
    tenure_for_optimizer = static_vars.get("tenure_for_optimizer_function")
    monthly_c_raw = static_vars.get("monthly_contribution", 1500)
    try:
        monthly_contribution = float(monthly_c_raw)
    except ValueError:
        monthly_contribution = 1500.0  # fallback default

    goal_amount_c_raw = static_vars.get("goal_amount", 1000000)
    try:
        goal_amount = float(goal_amount_c_raw)
    except ValueError:
        goal_amount = 1500.0  # fallback default

    # Convert months → years if short term
    if plan_type.lower() == "long-term":
        tenure_num = int(tenure_for_optimizer * 12)
    else:
        tenure_num = int(tenure_for_optimizer)

        # --- 2. Execute optimizer synchronously ---
    top_allocations, required_return = portfolio_optimizer(
        monthly_contribution=monthly_contribution,
        monthsCount=tenure_num,
        goal=goal_amount,
        funds=funds,
        top_n=2
    )

        # --- 3. Convert to JSON-safe dict for LLM ---
    if required_return is None:
        result_dict = {
            "required_return": "Target unreachable",
            "top_allocations": []
        }
    else:
        result_dict = {
            "required_return": f"{required_return * 100:.2f}%",
            "top_allocations": top_allocations.to_dict(orient="records")  # JSON-safe
        }

# --- 4. Prepare prompt for LLM to format as Markdown table ---
    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

    prompt_template = """
You are a financial assistant. Format the following portfolio optimization result into a **clean Markdown table**.

Required Return: {required_return}

Top Allocations (fund name and weight):
{top_allocations}

Notes:
- Show weights as percentages with % symbol.
- Include a table header.
- Keep it concise and professional.
- Explain clearly what exactly it is in theoretical manner.
"""
    # Convert allocations to simple readable string
    if result_dict["top_allocations"]:
        allocations_str = ""
        for item in result_dict["top_allocations"]:
            # Use the DataFrame column names from your optimizer
            # e.g., "Combination" and "Weights"
            combo = item.get("Combination", "N/A")
            weights = item.get("Weights", "N/A")
            allocations_str += f"{combo} -> {weights}\n"
    else:
        allocations_str = "No feasible allocations"

    prompt_filled = prompt_template.format(
        required_return=result_dict["required_return"],
        top_allocations=allocations_str
    )

    # --- 5. Generate formatted Markdown table via LLM ---
    formatted_md = {"result" : llm.predict(prompt_filled)}

    # --- 6. Return final Markdown for Streamlit display ---
    return formatted_md
