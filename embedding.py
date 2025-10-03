import os
import getpass
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from fastembed import TextEmbedding

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google API key: ")

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

def embed_text(text: str):
    return embeddings.embed_query(text)

def embed_texts(texts: list[str]):
    return embeddings.embed_documents(texts)
    

def embed_text_with_fastEmbed(text: list[str]):
    embedder = TextEmbedding()
    return list(embedder.embed(text))
