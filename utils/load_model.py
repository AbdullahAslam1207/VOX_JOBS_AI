from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

# Initialize embeddings model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def load_jobs_vector_store():
    """Load Jobs ChromaDB vector store from local path."""
    try:
        vectorstore = Chroma(
            persist_directory="vector_store/all_jobs_db",
            embedding_function=embeddings,
            collection_name="jobs_collection"
        )
        
        if vectorstore:
            print("[SUCCESS] Jobs vector store loaded successfully.")
            print(f"Doc count: {vectorstore._collection.count()}")
        else:
            print("[ERROR] ChromaDB load returned None.")
        
        return vectorstore
    except Exception as e:
        print(f"[ERROR] Failed to load Jobs vector store: {str(e)}")
        return None