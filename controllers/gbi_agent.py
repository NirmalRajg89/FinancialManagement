import os

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai  import ChatOpenAI
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from langchain.chains import ConversationalRetrievalChain

load_dotenv()

QDRANT_URL=os.getenv('QDRANT_URL')
QDRANT_API_KEY=os.getenv('QDRANT_API_KEY')

def GBI_RAG_agent(question, memory=None):
    embeddings = OpenAIEmbeddings()

    # Step 1: Qdrant client
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    # Step 2: Langchain wrapper for retriever
    qdrant = Qdrant(
        client=client,
        collection_name="GBI_docs",
        embeddings=embeddings,
        content_payload_key="text",
    )
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "You are a helpful assistant that answers clearly and concisely. "
            "Use bullet points, numbered steps, or markdown tables.\n\n"
            "Use the following context to answer the question:\n{context}\n\n"
            "Question: {question}"
        )
    )
    retriever = qdrant.as_retriever()

    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=False,
        combine_docs_chain_kwargs={"prompt": prompt},
        verbose=True  # Optional for debugging
    )
    response = qa_chain.invoke({"question": question})
    return {"result": response["answer"]}
