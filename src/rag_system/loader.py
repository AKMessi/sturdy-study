from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
from langchain.docstore.document import Document

def load_and_split_pdf(file_path: str) -> List[Document]:
    """
    Loads a PDF from the given file path and splits it into chunks.
    """
    
    try:
        # loading the pdf
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        if not documents:
            raise ValueError("PDF loaded 0 documents. The file might be empty, corrupted, or password-protected.")
        
        # splitting the text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200
        )
        split_docs = text_splitter.split_documents(documents)
        
        if not split_docs:
            raise ValueError("Failed to split documents. The PDF may be image-based (scanned) and contain no extractable text.")
            
        
        filtered_docs = [
            doc for doc in split_docs if doc.page_content and doc.page_content.strip()
        ]
        
        if not filtered_docs:
            raise ValueError("PDF content was filtered out. The document may contain only whitespace, headers/footers, or other non-substantive text.")
        
        print(f"[Loader] Loaded, split, and filtered {len(filtered_docs)} documents from {file_path}")
        
        return filtered_docs
        
    except Exception as e:
        print(f"Error loading/splitting PDF {file_path}: {e}")
        raise e