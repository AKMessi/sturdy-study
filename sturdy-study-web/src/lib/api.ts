import axios, { AxiosInstance } from 'axios';

// ============================================================================
// TypeScript Interfaces (matching Pydantic models)
// ============================================================================

export interface UploadResponse {
  filename: string;
  message: string;
  documents_added: number;
}

export interface ChatRequest {
  question: string;
  user_id: string;
}

export interface ChatResponse {
  answer: string | null;
  quiz: string | null;
  user_id: string;
  question: string;
}

export interface SearchRequest {
  topic: string;
  user_id: string;
}

export interface SearchResponse {
  results: string;
  user_id: string;
  topic: string;
}

export interface PrioritizeRequest {
  user_id: string;
}

export interface PrioritizeResponse {
  topics_list: string;
  user_id: string;
}

export interface ExamJob {
  job_id: string;
  status: string;
  download_url: string | null;
  error: string | null;
}

export interface ExamRequest {
  user_id: string;
  num_questions?: number; // default 20, must be > 0 and <= 50
}

export interface GuidedChatRequest {
  user_id: string;
  topic: string;
  chat_history: Array<{ role: string; content: string; [key: string]: any }>;
  user_question: string;
}

export interface GuidedChatResponse {
  ai_message: string;
}

export interface MapRequest {
  user_id: string;
}

export interface MapResponse {
  dot_string: string;
  user_id: string;
}

export interface YouTubeRequest {
  url: string;
  user_id: string;
}

// ============================================================================
// Axios Client Setup
// ============================================================================

const apiClient: AxiosInstance = axios.create({
  baseURL: 'http://localhost:8000/v1/study',
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// API Functions
// ============================================================================

/**
 * Upload a PDF file.
 * It will be processed and added to a user-specific vector store collection.
 */
export async function uploadPdf(
  user_id: string,
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', user_id);

  const response = await apiClient.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

/**
 * Upload an audio file (e.g., mp3, m4a, wav).
 * It will be transcribed, processed, and added to the user's vector store.
 */
export async function uploadAudio(
  user_id: string,
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', user_id);

  const response = await apiClient.post<UploadResponse>('/upload-audio', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

/**
 * Chat with the agent.
 * The agent will decide whether to answer a question or generate a quiz.
 */
export async function chat(request: ChatRequest): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>('/chat', request);
  return response.data;
}

/**
 * Find relevant practice problems from the web.
 * This endpoint uses RAG to power a Firecrawl search-and-scrape
 * for maximum relevance.
 */
export async function findProblems(request: SearchRequest): Promise<SearchResponse> {
  const response = await apiClient.post<SearchResponse>('/find-problems', request);
  return response.data;
}

/**
 * Analyzes ALL documents for a user to find the most important topics.
 * This is a heavy, one-time operation.
 */
export async function prioritizeTopics(request: PrioritizeRequest): Promise<PrioritizeResponse> {
  const response = await apiClient.post<PrioritizeResponse>('/prioritize', request);
  return response.data;
}

/**
 * Starts a background job to generate a PDF exam.
 * Returns a job_id to check status.
 */
export async function startExamGeneration(request: ExamRequest): Promise<ExamJob> {
  const response = await apiClient.post<ExamJob>('/generate-test', request);
  return response.data;
}

/**
 * Checks the status of a running exam generation job.
 */
export async function getExamJobStatus(job_id: string): Promise<ExamJob> {
  const response = await apiClient.get<ExamJob>(`/generate-test/status/${job_id}`);
  return response.data;
}

/**
 * Starts a new guided chat session with a topic.
 * This is a convenience function that calls guidedChat with an empty history.
 */
export async function startGuidedSession(
  user_id: string,
  topic: string
): Promise<GuidedChatResponse> {
  return guidedChat({
    user_id,
    topic,
    chat_history: [],
    user_question: `I want to learn about ${topic}`,
  });
}

/**
 * Manages a stateful, Socratic guided chat session.
 */
export async function guidedChat(request: GuidedChatRequest): Promise<GuidedChatResponse> {
  const response = await apiClient.post<GuidedChatResponse>('/guided-chat', request);
  return response.data;
}

/**
 * Analyzes ALL documents for a user to generate a Graphviz DOT
 * string for a concept map.
 */
export async function generateMap(request: MapRequest): Promise<MapResponse> {
  const response = await apiClient.post<MapResponse>('/generate-map', request);
  return response.data;
}

/**
 * Process a YouTube video (Transcript or Whisper) and add to vector DB.
 */
export async function processYouTube(request: YouTubeRequest): Promise<UploadResponse> {
  const response = await apiClient.post<UploadResponse>('/process-youtube', request);
  return response.data;
}

