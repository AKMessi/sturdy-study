from langchain_community.tools.tavily_search import TavilySearchResults
from src.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableMap, RunnablePassthrough
from langchain_core.runnables import RunnableLambda
from src.rag_system.vector_store import get_retriever
from src.rag_system.chain import _format_context
import json
import os

# setup: llm and tools
os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY

llm_flash = ChatGoogleGenerativeAI(
    model="gemini-flash-latest", 
    temperature=0,
    google_api_key=settings.GOOGLE_API_KEY
)
llm_pro = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro", 
    temperature=0.3,
    google_api_key=settings.GOOGLE_API_KEY
)

# initializing the tavily tool
tavily_tool = TavilySearchResults(max_results=5)


# refining the search query
QUERY_SYNTH_PROMPT = """
You are an expert search query creator.
Based on the user's TOPIC and their personal course CONTEXT, create a single, highly-specific Google search query
to find the most relevant practice problems.

TOPIC: {topic}
CONTEXT: {context}

Search Query:
"""
query_synth_prompt = PromptTemplate.from_template(QUERY_SYNTH_PROMPT)
query_synth_chain = query_synth_prompt | llm_flash | StrOutputParser()


# analyzes the search results
ANALYZE_RESULTS_PROMPT = """
You are an expert AI study assistant named "Sturdy Study".
Your user asked for practice problems on "{topic}".
You have used the Tavily search tool to find the most relevant web results.

SEARCH RESULTS (snippets, sources, and URLs):
{search_results}

Your task is to analyze these results and present a clean, helpful list.
- **Filter aggressively.** Your reputation depends on relevance.
- **Find the top 3-5 *most relevant* links** that point to *actual* practice problems or exam questions.
- For each link, provide the URL and the 'snippet' (a 1-sentence explanation of *why* it's relevant).
- If you find no relevant results, state that.
- **Do NOT make up your own problems.** If the search tool fails or finds nothing, just say so.

Your final, clean output (in Markdown format):
"""
analyze_results_prompt = PromptTemplate.from_template(ANALYZE_RESULTS_PROMPT)
analyze_results_chain = analyze_results_prompt | llm_pro | StrOutputParser()


# the full rag chain

def create_rag_search_chain():
    
    setup_chain = RunnableMap({
        "topic": lambda x: x["topic"],
        "context": (
            (lambda x: get_retriever(collection_name=x["user_id"])
            .invoke(x["topic"]))
            | RunnableLambda(_format_context)
        )
    })
    
    search_query_chain = RunnableMap({
        "topic": lambda x: x["topic"],
        "search_query": (
            setup_chain
            | query_synth_chain
        )
    })
    
    # this chain runs the search
    run_search_chain = RunnableMap({
        "topic": lambda x: x["topic"],
        
        "search_results": (
            (lambda x: x["search_query"])
            | tavily_tool
        )
    })
    
    # the full chain
    full_chain = (
        search_query_chain
        | run_search_chain
        | analyze_results_chain
    )
    
    return full_chain

# our runnable
rag_search_runnable = create_rag_search_chain()

def get_rag_search_runnable():
    return rag_search_runnable