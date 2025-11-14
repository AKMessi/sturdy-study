from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document
from typing import List, Optional
from langchain.vectorstores.base import VectorStoreRetriever
import os
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_PERSIST_DIR = "chroma_db"
DEFAULT_COLLECTION_NAME = "study_collection"

print("[Embeddings] Initializing HuggingFace local embeddings model...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)
print("[Embeddings] HuggingFace model loaded.")

try:
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    print(f"[VectorStore] Connected to persistent client at '{CHROMA_PERSIST_DIR}'")
except Exception as e:
    print(f"[VectorStore] CRITICAL ERROR: Could not connect to ChromaDB at '{CHROMA_PERSIST_DIR}'. {e}")
    client = None

# private helper function
def _get_vector_store(collection_name: str = DEFAULT_COLLECTION_NAME) -> Chroma:
    """
    Initializes and returns a Chroma vector store instance
    using our persistent client.
    """
    if client is None:
        raise Exception("ChromaDB client is not initialized.")
        
    return Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings,
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

def get_all_documents(collection_name: str = DEFAULT_COLLECTION_NAME) -> List[Document]:
    """
    Retrieves ALL documents (text and metadata) from a specific collection.
    """
    
    print(f"[VectorStore] Retrieving ALL documents from collection '{collection_name}'")
    try:
        if client is None:
            raise Exception("ChromaDB client is not initialized.")
            
        # use the client to get the collection
        collection = client.get_collection(name=collection_name)
        
        # get all data from the collection
        data = collection.get(include=["documents", "metadatas"])
        
        docs_list = []
        for i, doc_text in enumerate(data['documents']):
            docs_list.append(
                Document(
                    page_content=doc_text,
                    metadata=data['metadatas'][i]
                )
            )
            
        print(f"[VectorStore] Found {len(docs_list)} total documents.")
        return docs_list

    except Exception as e:
        print(f"Error retrieving all documents: {e}")
        return []