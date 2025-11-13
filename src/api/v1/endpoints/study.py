from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from pydantic import BaseModel
import os
import shutil
from src.rag_system.loader import load_and_split_pdf
from src.rag_system.vector_store import add_documents_to_store
from src.rag_system.graph import get_agent_runnable, AgentState

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