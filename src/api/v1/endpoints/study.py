from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from pydantic import BaseModel
import os
import shutil
from src.rag_system.loader import load_and_split_pdf, transcribe_and_split_audio
from src.rag_system.vector_store import add_documents_to_store
from src.rag_system.graph import get_agent_runnable, AgentState
from src.rag_system.search_chain import get_rag_search_runnable
from src.rag_system.prioritize_chain import get_prioritize_runnable
from fastapi import BackgroundTasks
from pydantic import BaseModel, Field
import uuid
from src.rag_system.exam_chain import generate_exam_and_pdf
from src.rag_system.tutor_chain import get_tutor_runnable
from typing import List, Dict, Any
from src.rag_system.map_chain import get_map_runnable
from src.rag_system.loader import process_youtube_video

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
    results: str 
    user_id: str
    topic: str

class PrioritizeRequest(BaseModel):
    user_id: str

class PrioritizeResponse(BaseModel):
    topics_list: str
    user_id: str

class ExamJob(BaseModel):
    job_id: str
    status: str = "pending"
    download_url: str | None = None
    error: str | None = None

class ExamRequest(BaseModel):
    user_id: str
    num_questions: int = Field(default=20, gt=0, le=50)

class GuidedChatRequest(BaseModel):
    user_id: str
    topic: str
    chat_history: List[Dict[str, Any]] # e.g., [{"role": "user", "content": "..."}, ...]
    user_question: str

class GuidedChatResponse(BaseModel):
    ai_message: str

class MapRequest(BaseModel):
    user_id: str

class MapResponse(BaseModel):
    dot_string: str # This will be the "digraph G { ... }" text
    user_id: str

class YouTubeRequest(BaseModel):
    url: str
    user_id: str

exam_jobs: dict[str, ExamJob] = {}

def run_exam_task(job_id: str, user_id: str, num_questions: int):
    """
    The function that runs in the background.
    It updates the job status in our 'exam_jobs' dict.
    """
    try:
        download_url = generate_exam_and_pdf(user_id, num_questions)
        exam_jobs[job_id].status = "complete"
        exam_jobs[job_id].download_url = download_url
    except Exception as e:
        exam_jobs[job_id].status = "error"
        exam_jobs[job_id].error = str(e)

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
    
@router.post("/prioritize", response_model=PrioritizeResponse)
async def prioritize_topics(request: PrioritizeRequest):
    """
    Analyzes ALL documents for a user to find the most important topics.
    This is a heavy, one-time operation.
    """
    try:
        # getting the runnable
        chain = get_prioritize_runnable()
        
        # defining the input
        input_data = {"user_id": request.user_id}
        
        # invoking the chain
        topics_list = chain.invoke(input_data)
        
        return PrioritizeResponse(
            topics_list=topics_list,
            user_id=request.user_id
        )
    
    except Exception as e:
        raise HTTPException(500, f"Error prioritizing topics: {e}")
    
@router.post("/generate-test", response_model=ExamJob)
async def start_exam_generation(
    request: ExamRequest,
    background_tasks: BackgroundTasks
):
    """
    Starts a background job to generate a PDF exam.
    Returns a job_id to check status.
    """

    # creating a unique job id
    job_id = str(uuid.uuid4())
    
    # creating the job function
    job = ExamJob(job_id=job_id, status="running")
    exam_jobs[job_id] = job
    
    # adding the heavy lift function
    background_tasks.add_task(
        run_exam_task, 
        job_id, 
        request.user_id, 
        request.num_questions
    )
    
    # returning the job status
    return job

@router.get("/generate-test/status/{job_id}", response_model=ExamJob)
async def get_exam_job_status(job_id: str):
    """
    Checks the status of a running exam generation job.
    """
    job = exam_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/guided-chat", response_model=GuidedChatResponse)
async def guided_chat_session(request: GuidedChatRequest):
    """
    Manages a stateful, Socratic guided chat session.
    """
    try:
        # getting the runnable
        chain = get_tutor_runnable()
        
        # defining the input
        input_data = {
            "user_id": request.user_id,
            "topic": request.topic,
            "chat_history": request.chat_history,
            "user_question": request.user_question
        }
        
        #invoking the chain
        ai_message = chain.invoke(input_data)
        
        return GuidedChatResponse(ai_message=ai_message)
    
    except Exception as e:
        raise HTTPException(500, f"Error in guided session: {str(e)}")
    
@router.post("/generate-map", response_model=MapResponse)
async def generate_concept_map(request: MapRequest):
    """
    Analyzes ALL documents for a user to generate a Graphviz DOT
    string for a concept map.
    """

    try:
        chain = get_map_runnable()
        
        input_data = {"user_id": request.user_id}
        
        dot_string = chain.invoke(input_data)
        
        if not dot_string.strip().startswith("digraph"):
            raise Exception("Failed to generate valid DOT string from LLM.")
        
        return MapResponse(
            dot_string=dot_string,
            user_id=request.user_id
        )
    
    except Exception as e:
        raise HTTPException(500, f"Error generating map: {str(e)}")
    
@router.post("/process-youtube", response_model=UploadResponse)
async def process_youtube(request: YouTubeRequest):
    """
    Process a YouTube video (Transcript or Whisper) and add to vector DB.
    """
    try:
        # process the video
        split_docs = process_youtube_video(request.url)
        
        # adding to vector store
        add_documents_to_store(split_docs, collection_name=request.user_id)
        
        return UploadResponse(
            filename=request.url,
            message="YouTube video processed and added to knowledge base.",
            documents_added=len(split_docs)
        )
        
    except Exception as e:
        raise HTTPException(500, f"Error processing YouTube video: {str(e)}")