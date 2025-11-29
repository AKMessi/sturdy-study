from src.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from src.rag_system.vector_store import get_all_documents
import re

# setup: llm
llm_pro = ChatGoogleGenerativeAI(
    model="gemini-flash-latest", 
    temperature=0.1,
    google_api_key=settings.GOOGLE_API_KEY
)

# helper function
def _format_context(docs: list) -> str:
    """
    Combines all documents into a single massive string.
    """
    return "\n\n---\n\n".join([doc.page_content for doc in docs])

# the concept map prompt
MAP_PROMPT = """
You are an expert in knowledge synthesis and graph theory.
Analyze the following "COURSE CONTEXT" and identify the top 10-15 core concepts.

Your task is to generate a "concept map" of how these topics relate to each other.

**Respond *only* with a text string in the Graphviz 'DOT' language.**
- Use `digraph G {{{{ ... }}}}`
- Use `rankdir="LR";` (Left-to-Right) for a good flow.
- Use `[label="..."]` to describe the relationship.
- Keep concepts in quotes (e.g., "Linear Regression").
- Do NOT add any other text, explanations, or markdown.

EXAMPLE:
digraph G {{{{
  rankdir="LR";
  "Linear Regression" -> "Cost Function" [label="is minimized by"];
  "Cost Function" -> "Gradient Descent" [label="optimizes"];
  "Gradient Descent" -> "Learning Rate" [label="is controlled by"];
}}}}

COURSE CONTEXT:
<CONTEXT>
{context}
</CONTEXT>

DOT Language Output:
"""

# the cleaner function
def _clean_dot_output(dot_string: str) -> str:
    """
    Cleans the LLM's output to ensure it's valid DOT.
    Removes markdown backticks and other junk.
    """

    match = re.search(r'digraph G {.*}', dot_string, re.DOTALL)
    if match:
        return match.group(0)
    
    return dot_string.strip().replace("```dot", "").replace("```", "")

# the full map chain
def create_map_chain():
    chain = (
        {
            "context": (
                (lambda x: x["user_id"])
                | RunnableLambda(get_all_documents)
                | RunnableLambda(_format_context)
            )
        }
        | PromptTemplate.from_template(MAP_PROMPT)
        | llm_pro
        | StrOutputParser()
        | RunnableLambda(_clean_dot_output)
    )
    return chain

# runnable
map_runnable = create_map_chain()

def get_map_runnable():
    return map_runnable