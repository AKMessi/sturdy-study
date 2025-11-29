from src.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from src.rag_system.vector_store import get_all_documents

# setup: llm

llm_pro = ChatGoogleGenerativeAI(
    model="gemini-flash-latest", 
    temperature=0.2,
    google_api_key=settings.GOOGLE_API_KEY
)

# helper function to format text
def _format_context(docs: list) -> str:
    """
    Helper function to combine retrieved documents into a single string.
    We add metadata (source file) to help the AI.
    """
    formatted_context = ""
    for doc in docs:
        source = doc.metadata.get('source', 'Unknown')
        formatted_context += f"[Source: {source}]\n{doc.page_content}\n\n---\n\n"
    return formatted_context

# the prioritization prompt
PRIORITIZE_PROMPT = """
You are an expert AI study-strategy assistant.
You have been given the complete text from a student's course, including all PDF slides and all audio lecture transcripts.

Here is the complete course context:
<CONTEXT>
{context}
</CONTEXT>

Your task is to analyze all of this information and identify the **Top 5-10 Most Important Topics** for an exam.

To do this, you must look for the following signals:
1.  **Emphasis:** Topics that are repeated many times across different sources (e.g., in both slides and audio).
2.  **Time Spent:** Topics where the lecture transcript is very long, indicating the professor spent a lot of time on it.
3.  **Signal Phrases:** Explicit cues in the audio transcripts like "this is important," "remember this," "this will be on the exam," or "this is a key concept."
4.  **Structure:** Core concepts that are major headings in the PDF slides.

Based on your analysis, return a ranked list of the most important topics. For each topic, provide a 1-sentence justification for *why* it's important, citing your evidence (e.g., "Professor spent 20 minutes on this," "Mentioned as 'key concept' in slides and audio," "Professor explicitly said 'this is on the exam'").

Format your response in Markdown.
"""

final_prompt_chain = (
    PromptTemplate.from_template(PRIORITIZE_PROMPT)
    | llm_pro
    | StrOutputParser()
)

# the full prioritization chain
def create_prioritize_chain():
    
    chain = (
        {
            "context": (
                (lambda x: x["user_id"])
                | RunnableLambda(get_all_documents)
                | RunnableLambda(_format_context)
            )
        }
        | final_prompt_chain
    )
    return chain

# runnable
prioritize_runnable = create_prioritize_chain()

def get_prioritize_runnable():
    return prioritize_runnable