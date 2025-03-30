from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
import json
import os

from config import INTERVIEW_LANGUAGE_MODEL
from prompts import REQUIREMENTS_EXTRACTION_PROMPT, INTERVIEW_QUESTIONS_PROMPT, ANSWER_EVALUATION_PROMPT
from utils import read_job_description, validate_job_description
from voice_utils import VoiceInterface 

class AgentState(TypedDict):
    job_description: str
    requirements: str
    questions: List[str]
    interview_log: List[Dict[str, Any]]
    current_question_index: int
    candidate_score: float
    interview_complete: bool
    needs_follow_up: bool

class VoiceRecruiterAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model=INTERVIEW_LANGUAGE_MODEL)
        self.voice_interface = VoiceInterface()  # Initialize voice interface
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
            "current_question_index": 0,
            "interview_complete": False
        }

    def ask_question(self, state: AgentState):
        """Select and prepare the next interview question using voice"""
        questions = state['questions']
        current_index = state['current_question_index']
        
        if current_index < len(questions):
            current_question = questions[current_index]
            
            # Use voice interface to speak the question
            print(f"\n[Interviewer Voice]: {current_question}")
            self.voice_interface.text_to_speech(current_question)
            
            return {
                "current_question_index": current_index + 1
            }
        else:
            # Final summary if interview is complete
            summary = self.generate_interview_summary(state)
            self.voice_interface.text_to_speech(summary)
            
            return {
                "interview_complete": True
            }

    def process_answer(self, state: AgentState):
        """Process candidate's voice answer and evaluate with follow-up capability"""
        # Record audio answer using voice interface
        print("\n[Interviewer]: Please speak your answer...")
        audio_path = self.voice_interface.record_audio()
        
        # Transcribe the audio answer
        candidate_answer = self.voice_interface.transcribe_audio(audio_path)
        print(f"[Transcribed Answer]: {candidate_answer}")
        
        # Prepare conversation context
        conversation_context = "\n".join([
            f"Question {i+1}: {entry['question']}\nAnswer: {entry['answer']}" 
            for i, entry in enumerate(state['interview_log'])
        ])
        
        # Evaluate answer using LLM
        evaluation_chain = ANSWER_EVALUATION_PROMPT | self.llm
        evaluation = evaluation_chain.invoke({
            "question": state['questions'][state['current_question_index'] - 1],
            "answer": candidate_answer,
            "context": conversation_context,
            "requirements": state['requirements']
        }).content
        
        # Parse evaluation
        try:
            eval_result = json.loads(evaluation)
            acknowledgment = eval_result.get('acknowledgment', '')
            needs_follow_up = eval_result.get('needs_follow_up', False)
            follow_up = eval_result.get('follow_up', '')
            score_increment = eval_result.get('score', 0)
        except Exception as e:
            print(f"Error parsing evaluation: {e}")
            acknowledgment = "Thank you for your answer."
            needs_follow_up = False
            follow_up = ""
            score_increment = 0
        
        # Provide verbal feedback
        response = acknowledgment
        if needs_follow_up:
            response += " " + follow_up
        
        print(f"[Interviewer Response]: {response}")
        self.voice_interface.text_to_speech(response)
        
        # Update interview log
        updated_log = state['interview_log'] + [{
            "question": state['questions'][state['current_question_index'] - 1],
            "answer": candidate_answer,
            "evaluation": evaluation,
            "needs_follow_up": needs_follow_up,
            "follow_up": follow_up if needs_follow_up else ""
        }]
        
        return {
            "interview_log": updated_log,
            "candidate_score": state.get('candidate_score', 0) + score_increment,
            "needs_follow_up": needs_follow_up,
            "interview_complete": state['current_question_index'] >= len(state['questions']) and not needs_follow_up
        }

    def handle_follow_up(self, state: AgentState):
        """Handle follow-up questions based on candidate's previous answer"""
        # If no follow-up needed, go back to asking the next question
        if not state.get('needs_follow_up', False):
            return {}
        
        # Get the last entry from the interview log
        last_entry = state['interview_log'][-1]
        follow_up = last_entry.get('follow_up', '')
        
        # Speak the follow-up question
        print(f"\n[Interviewer Follow-up]: {follow_up}")
        self.voice_interface.text_to_speech(follow_up)
        
        # Reset the needs_follow_up flag
        return {"needs_follow_up": False}

    def generate_interview_summary(self, state: AgentState):
        """Generate a summary of the interview"""
        try:
            summary_prompt = f"""
            Provide a concise summary of the interview based on the following details:
            - Total Questions: {len(state['questions'])}
            - Candidate Score: {state['candidate_score']}
            - Interview Log: {state['interview_log']}
            
            Highlight the candidate's strengths, areas of improvement, and overall performance.
            """
            
            summary_chain = self.llm.invoke(summary_prompt)
            return summary_chain.content
        except Exception as e:
            return f"Interview summary could not be generated. Error: {str(e)}"

    def build_graph(self):
        """Build the interview agent workflow graph"""
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("start", lambda state: state)
        workflow.add_node("extract_requirements", self.extract_requirements)
        workflow.add_node("generate_questions", self.generate_questions)
        workflow.add_node("ask_question", self.ask_question)
        workflow.add_node("process_answer", self.process_answer)
        workflow.add_node("handle_follow_up", self.handle_follow_up)

        # Set edges
        workflow.set_entry_point("start")
        workflow.add_edge("start", "extract_requirements")
        workflow.add_edge("extract_requirements", "generate_questions")
        workflow.add_edge("generate_questions", "ask_question")
        
        # Conditional edges for interview flow
        workflow.add_conditional_edges(
            "ask_question",
            lambda state: "end" if state['interview_complete'] else "process_answer",
            {
                "process_answer": "process_answer",
                "end": END
            }
        )
        
        # Add conditional edge for handling follow-ups
        workflow.add_conditional_edges(
            "process_answer",
            lambda state: "handle_follow_up" if state.get('needs_follow_up', False) else 
                        ("end" if state['interview_complete'] else "ask_question"),
            {
                "handle_follow_up": "handle_follow_up",
                "ask_question": "ask_question",
                "end": END
            }
        )
        
        # After follow-up, go back to process_answer
        workflow.add_edge("handle_follow_up", "process_answer")

        return workflow.compile()

    def run(self, job_description=None):
        """Run the interview agent"""
        if not job_description:
            job_description = read_job_description()
        
        # Welcome message via voice
        self.voice_interface.text_to_speech("Welcome to the interview. Let's begin!")
        
        initial_state = {
            "job_description": job_description,
            "requirements": "",
            "questions": [],
            "interview_log": [],
            "current_question_index": 0,
            "candidate_score": 0,
            "interview_complete": False
        }

        result = self.graph.invoke(initial_state)
        return result