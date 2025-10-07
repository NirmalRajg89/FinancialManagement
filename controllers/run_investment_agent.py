import time

import pandas as pd
import streamlit as st

from controllers.agent_controller_v1 import create_investment_summary_v1
from controllers.financial_advice_agent import create_financial_advice_agent


def make_json_safe(obj):
    """Recursively convert DataFrames to Markdown or dicts."""
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")  # or .to_markdown(index=False)
    elif isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    else:
        return obj

def run_investment_agent(static_vars, user_profile, plan_type, goals, risk_level, tenure, goal_amount, investment_options, monthly_contribution):
    # ---- 1️⃣ Create the main investment analysis agent ----
    st.session_state.agent = create_investment_summary_v1(static_vars)

    safe_static_vars = make_json_safe(static_vars)
    print("safe_static_vars", safe_static_vars)
    # Build the prompt for the first agent
    plan_prompt = {
        "profile": user_profile,
        "user_inputs": st.session_state.investment_input_data["user_inputs"],
        "tenure": f"{tenure} months" if plan_type == "Short-term" else f"{tenure} years",
        "monthly_contribution": monthly_contribution,
        "goal_amount": goal_amount,
        "risk_tolerance": risk_level,
        "investment_options": investment_options,
        "question": "Generate a detailed investment plan based on the above.",
        **safe_static_vars,
    }

    # ---- UI Streaming ----
    user_msg = f"Generate {plan_type} plan — goals: {goals}, tenure: {tenure} {'months' if plan_type == 'Short-term' else 'years'}, Goal to achieve: {goal_amount}"
    st.session_state.chat_history.append({"role": "user", "content": user_msg})

    response_placeholder = st.empty()
    full_response = ""

    # ---- Run the first agent ----
    analysis_response = st.session_state.agent.ask(plan_prompt)

    # Stream the response gradually
    for char in analysis_response:
        full_response += char
        # response_placeholder.markdown(full_response + "▌")
        time.sleep(0.001)

    # response_placeholder.markdown(full_response)
    # st.session_state.chat_history.append({"role": "assistant", "content": full_response})

    # Store the analysis result for the next agent
    st.session_state.analysis_output = full_response

    # ---- 2️⃣ Run the Financial Advisory Agent ----
    advice_agent = create_financial_advice_agent(safe_static_vars)
    advice_prompt = {
        "analysis_summary": st.session_state.analysis_output,
        "agent_scratchpad": "",
        **safe_static_vars
    }

    advice_placeholder = st.empty()
    advice_response_text = ""
    # st.markdown("### 🧭 Personalized Advisory Suggestions")

    # Run the second agent
    advice_response = advice_agent.ask(advice_prompt)

    # Stream the advisory response
    for char in advice_response:
        advice_response_text += char
        # advice_placeholder.markdown(advice_response_text + "▌")
        time.sleep(0.001)

    # advice_placeholder.markdown(advice_response_text)
    # st.session_state.chat_history.append({"role": "assistant", "content": advice_response_text})
    st.session_state.advice_output = advice_response_text

    # ---- 3️⃣ Combine Final Outputs ----
    final_output = f"### Investment Analysis\n\n{full_response}\n\n---\n\n{advice_response_text}"
    st.session_state.final_summary = final_output
    # st.session_state.chat_history.append({"role": "assistant", "content": final_output})

    return final_output
