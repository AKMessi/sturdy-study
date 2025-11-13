from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from pydantic import BaseModel
import os
import shutil
from src.rag_system.loader import load_and_split_pdf, transcribe_and_split_audio
from src.rag_system.vector_store import add_documents_to_store
from src.rag_system.graph import get_agent_runnable, AgentState
from src.rag_system.search_chain import get_rag_search_runnable

# setup
router = APIRouter()
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class UploadResponse(BaseModel):
    filename: str
    message: str
    documents_added: int

class ChatRequest(BaseModel):
    question: str
    user_id: str

class ChatResponse(BaseModel):
    answer: str | None = None
    quiz: str | None = None
    user_id: str
    question: str

class SearchRequest(BaseModel):
    topic: str
    user_id: str

class SearchResponse(BaseModel):
    results: str  # This will be the formatted Markdown string
    user_id: str
    topic: str

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    user_id: str = Body(...),
    file: UploadFile = File(...)
):
    """
    Upload a PDF file.
    It will be processed and added to a user-specific vector store collection.
    """

    if file.content_type != "application/pdf":
        raise HTTPException(400, "File must be a PDF")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        # saving the file temporarily
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # loading and splitting
        split_docs = load_and_split_pdf(file_path)
            
        # adding to the vector store
        add_documents_to_store(split_docs, collection_name=user_id)
        
        return UploadResponse(
            filename=file.filename,
            message="File processed and added to vector store.",
            documents_added=len(split_docs)
        )
        
    except Exception as e:
        raise HTTPException(500, f"An error occurred: {str(e)}")
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/upload-audio", response_model=UploadResponse)
async def upload_audio(
    user_id: str = Body(...),
    file: UploadFile = File(...)
):
    """
    Upload an audio file (e.g., mp3, m4a, wav).
    It will be transcribed, processed, and added to the user's vector store.
    """
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        # saving the file temporarily
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # transcribe and split
        split_docs = transcribe_and_split_audio(
            file_path, 
            source_filename=file.filename
        )
            
        # adding to the vector store
        add_documents_to_store(split_docs, collection_name=user_id)
        
        return UploadResponse(
            filename=file.filename,
            message="Audio file transcribed and added to vector store.",
            documents_added=len(split_docs)
        )
        
    except Exception as e:
        raise HTTPException(500, f"An error occurred: {str(e)}")
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/chat", response_model=ChatResponse)
async def chat_with_docs(request: ChatRequest):
    """
    Chat with the agent.
    The agent will decide whether to answer a question or generate a quiz.
    """
    try:
        # getting the agent runnable
        agent = get_agent_runnable()
        
        # defining the initial state
        initial_state: AgentState = {
            "question": request.question,
            "user_id": request.user_id,
            "answer": "",
            "quiz": "",
            "next_node": "router"
        }
        
        # invoking the state
        final_state = agent.invoke(initial_state)
        
        # return the result from the final state
        return ChatResponse(
            answer=final_state.get("answer"),
            quiz=final_state.get("quiz"),
            user_id=request.user_id,
            question=request.question
        )
    
    except Exception as e:
        raise HTTPException(500, f"Error during chat: {str(e)}")
    
@router.post("/find-problems", response_model=SearchResponse)
async def find_problems(request: SearchRequest):
    """
    Find relevant practice problems from the web.
    This endpoint uses RAG to power a Firecrawl search-and-scrape
    for maximum relevance.
    """
    
    try:
        # get the runnable
        search_chain = get_rag_search_runnable()
        
        # defining the input
        input_data = {
            "topic": request.topic,
            "user_id": request.user_id
        }
        
        # invoking the chain
        results = search_chain.invoke(input_data)
        
        return SearchResponse(
            results=results,
            user_id=request.user_id,
            topic=request.topic
        )
    
    except Exception as e:
        raise HTTPException(500, f"Error finding problems: {str(e)}")