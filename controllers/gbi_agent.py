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
    try:
        # Initialize embeddings
        embeddings = OpenAIEmbeddings()

        # Initialize Qdrant client
        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )

        # Create Qdrant retriever
        qdrant = Qdrant(
            client=client,
            collection_name="GBI_docs",
            embeddings=embeddings,
            content_payload_key="text",
        )

        # Define improved prompt template
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=(
                "You are a helpful assistant that answers questions clearly and concisely in a single well-structured response.\n"
                "Format your answer using bullet points, numbered steps, or markdown tables when appropriate.\n"
                "Provide only one complete answer that incorporates all relevant information.\n\n"
                "Context:\n{context}\n\n"
                "Question: {question}\n"
                "Answer:"
            )
        )

        retriever = qdrant.as_retriever()
        llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

        if memory:
            # Use conversational chain if memory is provided
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                memory=memory,
                return_source_documents=False,
                combine_docs_chain_kwargs={"prompt": prompt},
                rephrase_question=False,  # Prevents duplicate generation
                verbose=False
            )
            response = qa_chain.invoke({"question": question})
            return {"result": response["answer"]}
        else:
            # Use simpler QA chain if no memory needed
            qa = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                chain_type_kwargs={"prompt": prompt},
                return_source_documents=False
            )
            response = qa.invoke({"query": question})
            return {"result": response["result"]}

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
