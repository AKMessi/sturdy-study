from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document
from typing import List, Optional
from langchain.vectorstores.base import VectorStoreRetriever
import os

CHROMA_PERSIST_DIR = "chroma_db"
DEFAULT_COLLECTION_NAME = "study_collection"

print("[Embeddings] Initializing HuggingFace local embeddings model...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)
print("[Embeddings] HuggingFace model loaded.")

# private helper function
def _get_vector_store(collection_name: str = DEFAULT_COLLECTION_NAME) -> Chroma:
    """
    Initializes and returns a persistent Chroma vector store instance.
    """
    return Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
        collection_name=collection_name
    )

def add_documents_to_store(docs: List[Document], collection_name: str = DEFAULT_COLLECTION_NAME):
    """
    Adds a list of documents to the persistent vector store.
    """
    
    print(f"[VectorStore] Adding {len(docs)} documents to collection '{collection_name}'...")
    vector_store = _get_vector_store(collection_name)
    vector_store.add_documents(docs)
    
    print(f"[VectorStore] Documents added successfully.")

def get_retriever(collection_name: str = DEFAULT_COLLECTION_NAME) -> VectorStoreRetriever:
    """
    Gets a retriever for a specific collection.
    
    A 'retriever' is a LangChain object that knows how to
    fetch relevant documents from the vector store.
    """

    print(f"[VectorStore] Initializing retriever for collection '{collection_name}'")
    vector_store = _get_vector_store(collection_name)
    
    return vector_store.as_retriever(search_kwargs={"k": 4})

def clear_collection(collection_name: str = DEFAULT_COLLECTION_NAME):
    """
    Utility function to clear/delete a collection.
    Useful for testing.
    """

    try:
        store = _get_vector_store(collection_name)
        store.delete_collection()
        
        print(f"[VectorStore] Collection '{collection_name}' cleared.")
    except Exception as e:
        print(f"Error clearing collection {collection_name}: {e}")