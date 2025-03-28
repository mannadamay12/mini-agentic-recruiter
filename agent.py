from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from config import INTERVIEW_LANGUAGE_MODEL
from prompts import REQUIREMENTS_EXTRACTION_PROMPT, INTERVIEW_QUESTIONS_PROMPT
from utils import read_job_description, validate_job_description

class AgentState(TypedDict):
    job_description: str
    requirements: str
    questions: List[str]
    interview_log: List[dict]
    current_question_index: int

class RecruiterAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model=INTERVIEW_LANGUAGE_MODEL)
        self.graph = self.build_graph()

    def extract_requirements(self, state: AgentState):
        """Extract key requirements from job description"""
        if not validate_job_description(state['job_description']):
            raise ValueError("Invalid job description")
        
        requirements_chain = REQUIREMENTS_EXTRACTION_PROMPT | self.llm
        requirements = requirements_chain.invoke({"job_description": state['job_description']}).content
        
        return {"requirements": requirements}

    def generate_questions(self, state: AgentState):
        """Generate interview questions based on requirements"""
        questions_chain = INTERVIEW_QUESTIONS_PROMPT | self.llm
        questions = questions_chain.invoke({"requirements": state['requirements']}).content
        
        # Split questions into a list
        questions_list = [q.strip() for q in questions.split('\n') if q.strip()]
        
        return {
            "questions": questions_list,
            "current_question_index": 0
        }

    def build_graph(self):
        """Build the interview agent workflow graph"""
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("start", lambda state: state)
        workflow.add_node("extract_requirements", self.extract_requirements)
        workflow.add_node("generate_questions", self.generate_questions)

        # Set edges
        workflow.set_entry_point("start")
        workflow.add_edge("start", "extract_requirements")
        workflow.add_edge("extract_requirements", "generate_questions")
        workflow.add_edge("generate_questions", END)

        return workflow.compile()

    def run(self, job_description=None):
        """Run the interview agent"""
        if not job_description:
            job_description = read_job_description()
        
        initial_state = {
            "job_description": job_description,
            "requirements": "",
            "questions": [],
            "interview_log": [],
            "current_question_index": -1
        }

        result = self.graph.invoke(initial_state)
        return result
