from firecrawl import FirecrawlApp
from src.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableMap, RunnablePassthrough
from langchain_core.runnables import RunnableLambda
from src.rag_system.vector_store import get_retriever
from src.rag_system.chain import _format_context
import json

# setup: llm and tools

llm_flash = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0,
    google_api_key=settings.GOOGLE_API_KEY
)

llm_pro = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro", 
    temperature=0.3,
    google_api_key=settings.GOOGLE_API_KEY
)

# initializing the firecrawl app
firecrawl = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)

# chain 1: refining the search query
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


# chain 2: running the firecrawl search
def run_firecrawl_search(query: str):
    """
    Runs a Firecrawl search and returns the clean Markdown content.
    """
    print(f"[Firecrawl] Running search for: {query}")
    try:
        search_results = firecrawl.search(
            query, 
            search_options={"limit": 5},
            page_options={"format": "markdown"}
        )
        
        all_markdown = "\n\n--- NEW PAGE --- \n\n".join(
            [result.get("markdown", "") for result in search_results]
        )
        
        if not all_markdown.strip():
            return "No content found."
            
        return all_markdown
    except Exception as e:
        print(f"Error in Firecrawl search: {e}")
        return f"An error occurred while searching: {e}"


# chain 3: analyze
ANALYZE_RESULTS_PROMPT = """
You are an expert AI study assistant named "Sturdy Study".
Your user asked for practice problems on "{topic}".
You have used Firecrawl to search the web and scrape the full Markdown content from the top results.

FULL SCRAPED CONTENT:
{scraped_content}

Your task is to analyze all of this content and present a clean, helpful list.
- **Filter aggressively.** Your reputation depends on relevance.
- **Find *only* the actual practice problems** or exam questions in the content.
- Ignore ads, navigation links, and irrelevant text.
- Format the problems you find clearly.
- If you find no relevant problems, state that.

Your final, clean output:
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
    
    run_search_chain = RunnableMap({
        "topic": lambda x: x["topic"],
        "scraped_content": (
            (lambda x: x["search_query"])
            | RunnableLambda(run_firecrawl_search)
        )
    })
    
    full_chain = (
        search_query_chain
        | run_search_chain
        | analyze_results_chain
    )
    
    return full_chain

# runnable
rag_search_runnable = create_rag_search_chain()

def get_rag_search_runnable():
    return rag_search_runnable