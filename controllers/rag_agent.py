
from langchain.prompts import ChatPromptTemplate
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from controllers.agent_controller import create_agent_executor
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
# Directory containing Rate.com PDFs
docs_dir = os.path.join(os.path.dirname(__file__), '..', 'Rate.com')
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
    response = llm.invoke(prompt)
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

# Load all PDFs in the directory
def load_ratecom_documents():
    docs = []
    for filename in os.listdir(docs_dir):
        if filename.lower().endswith('.pdf'):
            loader = PyPDFLoader(os.path.join(docs_dir, filename))
            docs.extend(loader.load())
    return docs

# Create FAISS vector store from documents
def create_faiss_vectorstore(docs):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(splits, embeddings)
    return vectorstore

# Create the RAG agent (retriever QA chain)
def create_rag_agent():
    docs = load_ratecom_documents()
    vectorstore = create_faiss_vectorstore(docs)
    retriever = vectorstore.as_retriever()
    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)
    return qa_chain

# Function to answer a question using the RAG agent
def answer_ratecom_question(question):
    qa_chain = create_rag_agent()
    result = qa_chain.invoke({"query": question})
    return result["result"]
