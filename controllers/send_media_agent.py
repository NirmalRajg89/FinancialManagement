import json
import os
import streamlit as st

from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.chat_models import ChatOpenAI
from models.tools import send_sms_tool, send_email_tool, send_whatsapp_tool
from dotenv import load_dotenv

def load_env():
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]


class InvestmentAgent:
    """Wrapper around AgentExecutor so we can safely add custom methods."""
    def __init__(self, executor: AgentExecutor):
        self.executor = executor

    def ask(self, question):
        """Passes a question to the agent and returns the answer."""
        if isinstance(question, dict):
            question = json.dumps(question, indent=2)

        result = self.executor.invoke({"question": question})
        return result["output"] if "output" in result else result

def send_media_agent(history: list = None):

    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

    tools = [
        send_sms_tool,
        send_email_tool,
        send_whatsapp_tool,
    ]

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        input_key="question",
        output_key="output",
    )

    # Preload history into memory if available
    if history:
        for msg in history:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                memory.chat_memory.add_user_message(content)
            elif role == "assistant":
                memory.chat_memory.add_ai_message(content)
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         """You are a financial assistant. When returning comparisons or structured data, format it as either JSON (array of objects) or a Markdown table. Avoid extra text.

    If the user requests to send the "goal plan summary", "investment plan summary", or similar:
    - Extract the most recent assistant message from the 'chat_history' (this is the summary).
    - Identify the requested delivery method (SMS, WhatsApp, or Email).
    - Extract the recipient contact information (phone number or email) from the user's message if provided.
    - If phone number or email is not provided, respond by asking for it.
    - Clean the message for SMS by removing markdown, tables, or other unsupported formatting.
    - Use the correct tool (`send_sms_tool`, `send_email_tool`, or `send_whatsapp_tool`) with the summary and contact detail.

    Examples:
    - If the user says: "Send the summary to +1234567890 via WhatsApp", use `send_whatsapp_tool(message, to_number=...)`.
    - If the user says: "Email the plan to me at example@example.com", use `send_email_tool(message, to_email=...)`.
    - If the user says: "Send via SMS", but doesn’t provide a number, ask them for the recipient's phone number.
    """),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    executor = AgentExecutor(agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        return_intermediate_steps=False)
    return {"result": str(InvestmentAgent(executor).ask({"question": st.session_state.get("question", [])}))}
