from src.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from src.rag_system.vector_store import get_all_documents
import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# setup: llm
llm_pro = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0.3,
    google_api_key=settings.GOOGLE_API_KEY
)

# helper function
def _format_context(docs: list) -> str:
    """
    Combines all documents into a single massive string.
    """
    formatted_context = ""
    for doc in docs:
        source = doc.metadata.get('source', 'Unknown')
        formatted_context += f"[Source: {source}]\n{doc.page_content}\n\n---\n\n"
    return formatted_context

# the exam generation prompt
EXAM_PROMPT = """
You are a University Professor creating a final exam.
Based *only* on the provided course materials, generate **{num_questions}** high-quality, unique multiple-choice questions (MCQs) that cover the most important topics found in the context.

**Instructions:**
1.  Focus on the most important topics (judging by repetition, emphasis, and time spent).
2.  Each question must have four options (A, B, C, D).
3.  One option must be clearly correct based on the context.
4.  The other three options must be plausible but incorrect "distractors".
5.  Return *only* a single JSON object. Do not add any conversational text before or after.
6.  The JSON object must have one key: "questions", which is a list of objects.
7.  Each question object must have: "question_text", "options" (a list of 4 strings), and "correct_answer" (a string).

**EXAMPLE FORMAT:**
{{
  "questions": [
    {{
      "question_text": "What is the core idea of gradient descent?",
      "options": [
        "To maximize the cost function",
        "To iteratively move towards the minimum of a cost function",
        "To use a random search for parameters",
        "To set the learning rate to a large value"
      ],
      "correct_answer": "To iteratively move towards the minimum of a cost function"
    }}
  ]
}}

**COURSE MATERIALS:**
<CONTEXT>
{context}
</CONTEXT>

Generate {num_questions} MCQs now:
"""

exam_gen_prompt = PromptTemplate.from_template(EXAM_PROMPT)
exam_gen_chain = exam_gen_prompt | llm_pro | StrOutputParser()

# the pdf generation function
def create_exam_pdf(exam_data: dict, user_id: str) -> str:
    """
    Generates a two-page PDF (Exam + Answer Key) from the exam data
    and saves it to the static/exams/ folder.
    
    Returns the web-accessible download path.
    """
    
    filename = f"exam_{user_id}_{int(os.times().system)}.pdf"
    
    file_path = os.path.join("static", "exams", filename)
    
    download_url = f"/static/exams/{filename}"
    
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        spaceBefore=12,
        spaceAfter=6
    )
    
    option_style = ParagraphStyle(
        'Option',
        parent=styles['Normal'],
        leftIndent=0.5 * inch,
        spaceAfter=2
    )
    
    flowables = []
    answer_key = []

    flowables.append(Paragraph("Sturdy Study - Practice Exam", styles['h1']))
    flowables.append(Paragraph(f"Course ID: {user_id}", styles['Normal']))
    flowables.append(Spacer(1, 0.25 * inch))

    questions = exam_data.get("questions", [])
    for i, q in enumerate(questions):
        
        flowables.append(Paragraph(f"{i+1}. {q['question_text']}", question_style))
        
        for opt in q['options']:
            flowables.append(Paragraph(f"- {opt}", option_style))
            
        answer_key.append(f"{i+1}. {q['correct_answer']}")
        flowables.append(Spacer(1, 0.1 * inch))

    # answer key
    from reportlab.platypus import PageBreak
    flowables.append(PageBreak())
    flowables.append(Paragraph("Answer Key", styles['h1']))
    for answer in answer_key:
        flowables.append(Paragraph(answer, styles['Normal']))
    
    doc.build(flowables)
    print(f"[ExamGen] PDF created at {file_path}")
    return download_url

# the full exam generation logic
def generate_exam_and_pdf(user_id: str, num_questions: int) -> str:
    """
    The full, end-to-end logic for generating an exam.
    This function is designed to be run in a background thread.
    """

    print(f"[ExamGen] Starting exam generation for {user_id}...")
    
    # getting all documents
    docs = get_all_documents(user_id)
    if not docs:
        raise Exception("No documents found for this user.")
    
    # formatting them
    context = _format_context(docs)
    
    # calling the llm chain
    print("[ExamGen] Calling Gemini 2.5 Pro...")
    json_string = exam_gen_chain.invoke({
        "context": context,
        "num_questions": num_questions
    })
    
    # parsing the json
    try:
        clean_json_string = json_string.strip().replace("```json", "").replace("```", "")
        exam_data = json.loads(clean_json_string)
    except Exception as e:
        print(f"[ExamGen] Error parsing JSON: {e}")
        print(f"[ExamGen] Raw LLM Output: {json_string}")
        raise Exception("Failed to parse exam data from LLM.")
    
    # creating the pdf
    download_url = create_exam_pdf(exam_data, user_id)
    
    print(f"[ExamGen] Exam generation complete. URL: {download_url}")
    return download_url