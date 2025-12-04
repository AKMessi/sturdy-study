from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from src.rag_system.vector_store import get_retriever
from src.rag_system.chain import create_rag_chain, create_quiz_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from src.core.config import settings

# defining the agent state
class AgentState(TypedDict):
    question: str       # the user's original question
    user_id: str        # the user's collection ID
    answer: str         # the final answer (from RAG)
    quiz: str           # the final quiz (from Quiz generator)
    next_node: Literal["rag", "quiz", "end"] # what node to run next

# defining the graph nodes

def rag_node(state: AgentState):
    """
    Runs the RAG chain to answer a question.
    """
    print("---NODE: Running RAG Chain---")
    user_id = state["user_id"]
    question = state["question"]
    
    retriever = get_retriever(collection_name=user_id)
    rag_chain = create_rag_chain(retriever)
    
    answer = rag_chain.invoke({"question": question})
    
    return {"answer": answer, "next_node": "end"}

def quiz_node(state: AgentState):
    """
    Runs the Quiz chain to generate a quiz.
    """
    print("---NODE: Running Quiz Generator---")
    user_id = state["user_id"]
    question = state["question"] # e.g., "5 question quiz on Chapter 1"
    
    retriever = get_retriever(collection_name=user_id)
    quiz_chain = create_quiz_chain(retriever)
    
    quiz_json_str = quiz_chain.invoke({"question": question})
    
    return {"quiz": quiz_json_str, "next_node": "end"}

# defining the router

ROUTER_PROMPT_TEMPLATE = """
Analyze the user's question and decide which tool to use.
Respond with "rag" if the user is asking a question.
Respond with "quiz" if the user is asking to be quizzed or for a test.

User Question:
{question}

Your decision (rag or quiz):
"""
router_prompt = PromptTemplate.from_template(ROUTER_PROMPT_TEMPLATE)
router_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0,
    google_api_key=settings.GOOGLE_API_KEY
)

# routing logic
router_chain = router_prompt | router_llm | StrOutputParser()

def router_node(state: AgentState):
    """
    Decides the next node to run based on the user's question.
    """
    print("---NODE: Routing---")
    question = state["question"]
    decision = router_chain.invoke({"question": question})
    
    if "quiz" in decision.lower():
        print("---DECISION: quiz---")
        return {"next_node": "quiz"}
    else:
        print("---DECISION: rag---")
        return {"next_node": "rag"}

# building the graph

def create_agent_graph():
    """
    Creates and compiles the LangGraph agent.
    """

    workflow = StateGraph(AgentState)
    
    workflow.add_node("router", router_node)
    workflow.add_node("rag_node", rag_node)
    workflow.add_node("quiz_node", quiz_node)
    
    workflow.set_entry_point("router")
    
    workflow.add_conditional_edges(
        "router",
        lambda state: state["next_node"],
        {
            "rag": "rag_node",
            "quiz": "quiz_node"
        }
    )
    
    workflow.add_edge("rag_node", END)
    workflow.add_edge("quiz_node", END)
    
    # compiling the graph
    app = workflow.compile()
    return app

# create a single runnable
agent_runnable = create_agent_graph()

def get_agent_runnable():
    return agent_runnable