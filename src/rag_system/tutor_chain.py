from src.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableMap
from langchain_core.runnables import RunnableLambda
from src.rag_system.vector_store import get_retriever
from src.rag_system.chain import _format_context # Re-using this!

# --- NEW IMPORTS ---
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict, Any
# --- END NEW IMPORTS ---

# --- 1. Setup: LLM ---
llm_pro = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0.4,
    google_api_key=settings.GOOGLE_API_KEY
)

# --- 2. The "Tutor" Prompt ---
TUTOR_SYSTEM_PROMPT = """
You are "Sturdy Study", an expert AI tutor with a Socratic, encouraging style.
Your goal is to guide the student to mastery of a specific "{topic}".
You are an expert on the student's course, using their *own* "CONTEXT" (from their lectures and slides).

**Your Guiding Principles:**
1.  **NEVER** give the answer directly. Always ask one guiding question at a time.
2.  **START BASIC:** Your first question should be foundational (e.g., "In your own words, what is {topic}?").
3.  **USE THE CONTEXT:** When the user answers, cross-check their answer with the "CONTEXT".
4.  **IF THEY ARE RIGHT:** Acknowledge their correct point, then ask a *deeper* follow-up question. (e.g., "Exactly! And why is that important for...?").
5.  **IF THEY ARE WRONG/STUCK:** Gently correct them by pointing them to their *own* notes. (e.g., "Not quite. According to your professor's notes, it's actually... Why do you think that is?").
6.  **STAY ON TOPIC:** Keep the user focused on the "{topic}".

Here is the context from the student's course materials:
<CONTEXT>
{context}
</CONTEXT>

**The session starts now.**
"""
tutor_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(TUTOR_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{user_question}")
])

# --- 3. Chat History Parser ---
def _parse_chat_history(history_dicts: List[Dict[str, Any]]) -> List:
    """
    Converts a list of simple dicts into a list of LangChain BaseMessage objects.
    """
    messages = []
    for msg in history_dicts:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg.get("content", "")))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg.get("content", "")))
    return messages

# --- 4. The Full "Tutor" Chain (NEW SIMPLIFIED LOGIC) ---
def create_tutor_chain():
    
    # This chain will take the initial input: 
    # {"topic": "t", "user_id": "u", "chat_history": [...], "user_question": "..."}
    
    chain = (
        RunnableMap({
            # --- This runnable map builds ALL keys needed by the prompt ---
            
            # 1. Pass through the topic string
            "topic": lambda x: x["topic"],
            
            # 2. Pass through the user_question string
            "user_question": lambda x: x["user_question"],
            
            # 3. Parse the chat_history
            "chat_history": lambda x: _parse_chat_history(x["chat_history"]),
            
            # 4. Retrieve and format the context
            "context": 
                # This sub-chain runs on the original input `x`
                (lambda x: {
                    "retriever": get_retriever(collection_name=x["user_id"]),
                    "topic": x["topic"]
                })
                # The output dict is piped into this lambda
                | RunnableLambda(lambda y: y["retriever"].invoke(y["topic"]))
                # The list[docs] is piped into this lambda
                | RunnableLambda(_format_context)
        })
        | tutor_prompt
        | llm_pro
        | StrOutputParser()
    )
    
    return chain

# --- 5. Our runnable ---
tutor_runnable = create_tutor_chain()

def get_tutor_runnable():
    return tutor_runnable