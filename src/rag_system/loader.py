from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
from langchain.docstore.document import Document
import os
import whisper

print("[Whisper] Initializing Whisper transcription model...")
whisper_model = whisper.load_model("base")
print("[Whisper] Whisper model loaded.")

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
    
def transcribe_and_split_audio(file_path: str, source_filename: str) -> List[Document]:
    """
    Transcribes an audio file using Whisper and splits the text into chunks.
    """
    
    try:
        # transcribing the audio
        print(f"[Whisper] Transcribing {file_path}...")
        transcription_result = whisper_model.transcribe(file_path, fp16=False)
        full_text = transcription_result.get("text")
        
        if not full_text or not full_text.strip():
            raise ValueError("Audio transcription resulted in empty text. The file might be silent or corrupted.")
        
        print("[Whisper] Transcription complete.")
        
        # splitting the text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200
        )
        
        doc = Document(
            page_content=full_text,
            metadata={"source": source_filename}
        )
        
        split_docs = text_splitter.split_documents([doc])
        
        print(f"[Loader] Transcribed and split {len(split_docs)} documents from {file_path}")
        return split_docs

    except Exception as e:
        print(f"Error transcribing audio {file_path}: {e}")
        raise e