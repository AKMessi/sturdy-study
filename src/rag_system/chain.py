from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema.runnable import RunnableMap, RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from src.rag_system.vector_store import get_retriever
from langchain.vectorstores.base import VectorStoreRetriever
from src.core.config import settings
from langchain.prompts import ChatPromptTemplate, PromptTemplate

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.3,
    google_api_key=settings.GOOGLE_API_KEY
)

# prompt template
RAG_PROMPT_TEMPLATE = """
CONTEXT:
{context}

QUESTION:
{question}

Based *only* on the context provided, please answer the user's question.
If the context does not contain the answer, state "I do not have enough information from your documents to answer that."
Do not make up information.
"""

rag_prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

QUIZ_PROMPT_TEMPLATE = """
CONTEXT:
{context}

REQUEST:
{question}

You are an expert AI study assistant. Based *only* on the provided context, generate a {question}
Format the quiz as a JSON object with a single key "questions", which is a list of objects. 
Each object should have three keys: "question_text", "options" (a list of 4 strings), and "correct_answer" (a string).

Example Format:
{{
  "questions": [
    {{
      "question_text": "What is the capital of France?",
      "options": ["London", "Berlin", "Paris", "Madrid"],
      "correct_answer": "Paris"
    }}
  ]
}}
"""

quiz_prompt = PromptTemplate.from_template(QUIZ_PROMPT_TEMPLATE)

def create_quiz_chain(retriever: VectorStoreRetriever):
    """
    Creates a chain that generates a quiz.
    """
    
    retrieval_chain = RunnableMap({
        "context": lambda x: _format_context(retriever.invoke(x["question"])),
        "question": lambda x: x["question"]
    })
    
    quiz_chain = (
        retrieval_chain
        | quiz_prompt
        | llm
        | StrOutputParser()
    )
    return quiz_chain

# helper functions

def _format_context(docs: list) -> str:
    """
    Helper function to combine retrieved documents into a single string.
    """
    return "\n\n---\n\n".join([d.page_content for d in docs])

# the core rag chain

def create_rag_chain(retriever: VectorStoreRetriever):
    """
    Creates the main RAG chain using LCEL (LangChain Expression Language).
    """
    
    # runnablemap
    retrieval_chain = RunnableMap({
        "context": lambda x: _format_context(retriever.invoke(x["question"])),
        "question": lambda x: x["question"]
    })

    # the full chain
    rag_chain = (
        retrieval_chain
        | rag_prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain

def get_rag_chain(collection_name: str):
    """
    High-level function to get a runnable RAG chain for a specific collection.
    """
    retriever = get_retriever(collection_name)
    return create_rag_chain(retriever)