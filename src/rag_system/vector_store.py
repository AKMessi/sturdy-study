import os
import time
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from typing import List
from src.core.config import settings

INDEX_NAME = settings.PINECONE_INDEX_NAME

print("[Embeddings] Initializing HuggingFace embeddings...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

def _get_vector_store(namespace: str):
    """
    Returns a Pinecone Vector Store connected to our index.
    CRITICAL: We use 'namespace' to separate users.
    namespace = user_id (from Clerk)
    """

    os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY
    
    return PineconeVectorStore.from_existing_index(
        index_name=INDEX_NAME,
        embedding=embeddings,
        namespace=namespace 
    )


def add_documents_to_store(docs: List[Document], collection_name: str):
    """
    Adds documents to the user's specific namespace in Pinecone.
    """
    print(f"[VectorStore] Adding {len(docs)} docs to namespace: {collection_name}")
    
    if not docs:
        return

    try:
        PineconeVectorStore.from_documents(
            documents=docs,
            embedding=embeddings,
            index_name=INDEX_NAME,
            namespace=collection_name 
        )
        print(f"[VectorStore] Upload complete.")
    except Exception as e:
        print(f"[VectorStore] Error uploading to Pinecone: {e}")
        raise e

def get_retriever(collection_name: str):
    """
    Gets a retriever for the specific user namespace.
    """
    vector_store = _get_vector_store(collection_name)
    return vector_store.as_retriever(search_kwargs={"k": 10})

def get_all_documents(collection_name: str) -> List[Document]:
    """
    Retrieves documents for the 'Prioritize' and 'Exam' features.
    Pinecone doesn't support a simple 'get all', so we perform a 
    broad similarity search to fetch context.
    """
    vector_store = _get_vector_store(collection_name)
    return vector_store.similarity_search(".", k=100)

def clear_collection(collection_name: str):
    """
    Deletes all vectors in the user's namespace.
    """
    try:
        vector_store = _get_vector_store(collection_name)
        vector_store.delete(delete_all=True)
        print(f"[VectorStore] Namespace '{collection_name}' cleared.")
    except Exception as e:
        print(f"Error clearing namespace: {e}")