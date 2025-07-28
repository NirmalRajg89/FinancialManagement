import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_URL=os.getenv('QDRANT_URL')
QDRANT_API_KEY=os.getenv('QDRANT_API_KEY')


def Rate_RAG_agent(question, memory=None):
    embeddings = OpenAIEmbeddings()

    # Step 1: Qdrant client
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    # Step 2: Langchain wrapper for retriever
    qdrant = Qdrant(
        client=client,
        collection_name="Rate_docs",
        embeddings=embeddings,
        content_payload_key="text",  # or "page_content", if that's your field
    )

    retriever = qdrant.as_retriever()

    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=False,
        memory=memory,  # optionally include memory
    )

    return qa_chain.invoke(question)