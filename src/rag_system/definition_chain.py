from src.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableMap
from langchain_core.runnables import RunnableLambda
from src.rag_system.vector_store import get_retriever
from src.rag_system.chain import _format_context # Re-using this!

# setup: llm
llm_flash = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0,
    google_api_key=settings.GOOGLE_API_KEY
)

# the word for word prompt
DEFINITION_PROMPT = """
You are a definition extraction bot.
Based on the "CONTEXT" provided, find the single best, most concise, "word-for-word" definition for the user's "TERM".

- **You MUST quote the context directly.**
- Do NOT add any extra words, explanations, or conversational phrases.
- If you find multiple definitions, choose the clearest one.
- If you cannot find an exact definition in the context, respond with "I could not find a definition for that term in your documents."

CONTEXT:
{context}

TERM:
{term}

Exact Definition:
"""
definition_prompt = PromptTemplate.from_template(DEFINITION_PROMPT)

# definition chain
def create_definition_chain():
    
    chain = (
        {
            "term": lambda x: x["term"],
            "context": (
                lambda x: get_retriever(collection_name=x["user_id"])
                .invoke(x["term"])
            )
            | RunnableLambda(_format_context)
        }
        | definition_prompt
        | llm_flash
        | StrOutputParser()
    )
    return chain

# runnable
definition_runnable = create_definition_chain()

def get_definition_runnable():
    return definition_runnable