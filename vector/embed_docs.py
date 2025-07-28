import os
import hashlib

from dotenv import load_dotenv
import uuid
from qdrant_client.models import VectorParams, Distance

from langchain_community.document_loaders import UnstructuredMarkdownLoader, PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient

# Collections name gbi_agent -> GBI_docs && rate_agent -> Rate_docs

load_dotenv()

OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')
QDRANT_URL=os.getenv('QDRANT_URL')
QDRANT_API_KEY=os.getenv('QDRANT_API_KEY')

# 1. Load documents
docs = []

md_dir = os.path.join("..", "gbi_knowledge_base")  # folder parallel to 'vector/'

for file in os.listdir(md_dir):
    if file.endswith(".md") or file.endswith(".pdf"):
        path = os.path.join(md_dir, file)
        if file.endswith(".md"):
            loader = TextLoader(path)
        elif file.endswith(".pdf"):
            loader = PyPDFLoader(path)
        elif file.endswith(".txt"):
            loader = TextLoader(path)
        docs.extend(loader.load())

# 2. Split documents into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
splits = splitter.split_documents(docs)

# 3. Generate text chunks and deterministic IDs
def hash_chunk(doc):
    sha256_hash = hashlib.sha256(doc.page_content.encode("utf-8")).hexdigest()
    return str(uuid.UUID(sha256_hash[:32]))

ids = [hash_chunk(doc) for doc in splits]

# 4. Embed the text chunks
embeddings = OpenAIEmbeddings()
vectors = embeddings.embed_documents([doc.page_content for doc in splits])

# 5. Format payload for Qdrant
payload = [
    {"text": doc.page_content, **doc.metadata}
    for doc in splits
]

# 6. Upsert into Qdrant using native client
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

collection_name = "GBI_docs"

# Create collection if it doesn't exist
if not client.collection_exists(collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=1536,  # or 768 if using smaller embeddings like `text-embedding-3-small`
            distance=Distance.COSINE,
        ),
    )

client.upsert(
    collection_name=collection_name,
    points=[
        {
            "id": ids[i],
            "vector": vectors[i],
            "payload": payload[i],
        }
        for i in range(len(splits))
    ],
)

print(f"✅ Embedded and stored {len(splits)} documents in Qdrant collection '{collection_name}'.")
