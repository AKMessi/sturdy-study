from src.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.schema import StrOutputParser
from langchain.schema import RunnableMap
from langchain_core.runnables import RunnableLambda
from src.rag_system.vector_store import get_retriever
from src.rag_system.chain import _format_context
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict, Any

# setup: llm
llm_pro = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0.4,
    google_api_key=settings.GOOGLE_API_KEY
)

# the tutor prompt
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

# chat history parser
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

# the full tutor chain
def create_tutor_chain():
    
    chain = (
        RunnableMap({
            
            "topic": lambda x: x["topic"],
            
            "user_question": lambda x: x["user_question"],
            
            "chat_history": lambda x: _parse_chat_history(x["chat_history"]),
            
            "context": 
                (lambda x: {
                    "retriever": get_retriever(collection_name=x["user_id"]),
                    "topic": x["topic"]
                })
                | RunnableLambda(lambda y: y["retriever"].invoke(y["topic"]))
                | RunnableLambda(_format_context)
        })
        | tutor_prompt
        | llm_pro
        | StrOutputParser()
    )
    
    return chain

# runnable
tutor_runnable = create_tutor_chain()

def get_tutor_runnable():
    return tutor_runnable