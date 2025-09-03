from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# LLM-based classifier for routing
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

MEMORY_LOOKUP_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
        You are a helpful financial assistant with access to past conversation history.

        Here is the chat history:
        {chat_history}

        The user just asked: "{question}"

        Based on the conversation so far, can you answer this without needing new information?
        If yes, provide the answer directly. If not, say exactly: "NOT_FOUND".
    """)
])


def memory_agent(query, chat_history=None):
    # 1. Try to answer from memory
    if chat_history:
        # Run memory summarization check
        memory_prompt = MEMORY_LOOKUP_PROMPT.format_messages(
            chat_history=chat_history,
            question=query
        )
        memory_response = llm(memory_prompt)

        if hasattr(memory_response, "content"):
            memory_response = memory_response.content
            if memory_response == 'NOT_FOUND':
                return {
                    "result": "I'm here to assist with financial-investments-related questions only and this query seems to be out-of-scope."}
            return {"result": memory_response}

    return {
        "result": "I'm here to assist with financial-investments-related questions only and this query seems to be out-of-scope."}



