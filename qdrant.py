from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os

load_dotenv()

client = QdrantClient(url=os.getenv("QDRANT_URL"))

def add_documents(documents: list[str]):
    client.add(collection_name="document_chunks", documents=documents)

def search_document_chunks(query: str):
    return client.query(collection_name="document_chunks", query_text=query)

