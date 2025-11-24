from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Optional
from langchain.docstore.document import Document
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import yt_dlp
import whisper

print("[Whisper] Initializing Whisper transcription model...")
whisper_model = whisper.load_model("base")
print("[Whisper] Whisper model loaded.")

def get_youtube_video_id(url: str) -> Optional[str]:
    """Extracts video ID from various YouTube URL formats."""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

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
    
def fetch_youtube_transcript(video_id: str) -> Optional[str]:
    """
    Tries to fetch the transcript directly from YouTube.
    Returns the text string if found, or None.
    """
    
    print(f"[YouTube] Attempting to fetch transcript for {video_id}...")
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        
        full_text = " ".join([t['text'] for t in transcript_list])
        print("[YouTube] Transcript fetched successfully!")
        return full_text
    except Exception as e:
        print(f"[YouTube] No existing transcript found: {e}")
        return None

# the slow path (download + whisper)
def download_youtube_audio(url: str, output_dir: str = "temp_uploads") -> str:
    """
    Downloads the audio of a YouTube video using yt-dlp.
    Returns the path to the downloaded file.
    """
    print(f"[YouTube] Downloading audio from {url}...")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        final_filename = filename.rsplit('.', 1)[0] + '.mp3'
        
    print(f"[YouTube] Download complete: {final_filename}")
    return final_filename

# the main handler function
def process_youtube_video(url: str) -> List[Document]:
    """
    Orchestrates the YouTube processing:
    1. Try fetching transcript (Fast).
    2. If fail, download audio & Whisper it (Slow).
    """
    video_id = get_youtube_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")

    # trying fast path
    transcript_text = fetch_youtube_transcript(video_id)

    # if fast path failed, try slow path
    if not transcript_text:
        print("[YouTube] Falling back to Whisper transcription...")
        try:
            audio_path = download_youtube_audio(url)
            
            transcription = whisper_model.transcribe(audio_path, fp16=False)
            transcript_text = transcription.get("text")
            
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
        except Exception as e:
            raise Exception(f"Failed to process YouTube video: {e}")

    if not transcript_text:
         raise ValueError("Could not extract any text from this video.")

    # splitting text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    doc = Document(
        page_content=transcript_text,
        metadata={"source": f"YouTube: {url}"}
    )
    
    return text_splitter.split_documents([doc])