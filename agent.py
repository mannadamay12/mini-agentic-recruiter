from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
import json
import os
import time
from meeting_utils import join_google_meet
from config import INTERVIEW_LANGUAGE_MODEL, MAX_INTERVIEW_QUESTIONS, AGENT_VOICE
from prompts import (
    REQUIREMENTS_EXTRACTION_PROMPT, 
    INTERVIEW_QUESTIONS_PROMPT, 
    ANSWER_EVALUATION_PROMPT,
    INTERVIEW_SUMMARY_PROMPT
)
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
    in_meeting: bool
    current_summary: Optional[str]

class VoiceRecruiterAgent:
    def __init__(self, in_meeting=False, voice=AGENT_VOICE):
        # self.llm = ChatOpenAI(model=INTERVIEW_LANGUAGE_MODEL, temperature=0.7)
        # self.voice_interface = VoiceInterface()
        # self.graph = self.build_graph()
        # self.in_meeting = in_meeting
        # Initialize the voice interface
        self.voice_interface = VoiceInterface()
        self.in_meeting = in_meeting
        self.agent_voice = voice
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model=INTERVIEW_LANGUAGE_MODEL,
            temperature=0.7
        )
        
        # Build the agent workflow graph
        self.graph = self.build_graph()
        
        # If in meeting mode, set up meeting-specific configurations
        if in_meeting:
            print("[System] Agent initialized in meeting mode")
            # Adjust microphone settings for meeting context
            self.voice_interface.adjust_for_meeting()
    
    def prepare_for_meeting(self, meet_link):
        """Prepare the agent for a meeting context"""
        if not self.in_meeting:
            print("[System] Setting agent to meeting mode")
            self.in_meeting = True
        
        # Join the meeting
        join_success = join_google_meet(meet_link)
        
        if join_success:
            print("[System] Successfully joined meeting")
            # Brief pause to ensure audio systems initialize
            time.sleep(5)
            
            # Test audio output with a greeting
            intro_message = "Hello, I'm your AI interviewer today. Can you hear me clearly?"
            self.voice_interface.text_to_speech(intro_message, voice=self.agent_voice)
            
            # Wait for potential response
            time.sleep(3)
            return True
        else:
            print("[System] Failed to join meeting automatically")
            return False
        
    def initialize_interview(self, state: AgentState):
        """Initialize the interview with a welcome message"""
        welcome_message = (
            f"Hello! I'm your AI interviewer for today. "
            f"Thanks for joining this interview session. "
            f"I'll be asking you a few questions about your background and experience. "
            f"Feel free to take your time with your answers, and I may ask follow-up questions as we go. "
            f"Let's get started with the first question."
        )
        
        print(f"\n[AI Interviewer]: {welcome_message}")
        self.voice_interface.text_to_speech(welcome_message, voice=AGENT_VOICE)
        
        return {}

    def extract_requirements(self, state: AgentState):
        """Extract key requirements from job description"""
        if not validate_job_description(state['job_description']):
            raise ValueError("Invalid job description")
        
        print("\n[System] Analyzing job description...")
        requirements_chain = REQUIREMENTS_EXTRACTION_PROMPT | self.llm
        requirements = requirements_chain.invoke({"job_description": state['job_description']}).content
        
        return {"requirements": requirements}

    def generate_questions(self, state: AgentState):
        """Generate interview questions based on requirements"""
        print("\n[System] Generating interview questions...")
        questions_chain = INTERVIEW_QUESTIONS_PROMPT | self.llm
        questions = questions_chain.invoke({"requirements": state['requirements']}).content
        
        # Split questions into a list
        questions_list = [q.strip() for q in questions.split('\n') if q.strip()]

        # Remove any numbering (e.g., "1. ", "2. ")
        questions_list = [q.lstrip("0123456789. ") for q in questions_list]
        
        limited_questions = questions_list[:MAX_INTERVIEW_QUESTIONS]
        
        return {
            "questions": limited_questions,
            "current_question_index": 0,
            "interview_complete": False
        }

    def ask_question(self, state: AgentState):
        """Select and prepare the next interview question using voice"""
        questions = state['questions']
        current_index = state['current_question_index']
        
        if current_index < len(questions):
            current_question = questions[current_index]
            
            # Add a natural lead-in to the first question
            if current_index == 0:
                current_question = "For my first question, " + current_question
            
            # For middle questions, add some variety to transitions
            elif current_index < len(questions) - 1:
                transitions = [
                    "Great. Next, ",
                    "Thank you for sharing that. Let's move on to ",
                    "I appreciate your insights. Now I'd like to ask, ",
                    "That's helpful. My next question is, "
                ]
                import random
                current_question = transitions[random.randint(0, len(transitions)-1)] + current_question
            
            # For the last question
            else:
                current_question = "For my final question, " + current_question
            
            # Use voice interface to speak the question
            print(f"\n[AI Interviewer]: {current_question}")
            self.voice_interface.text_to_speech(current_question, voice=AGENT_VOICE)
            
            return {
                "current_question_index": current_index + 1
            }
        else:
            # Final summary if interview is complete
            print("\n[System] Preparing interview summary...")
            summary = self.generate_interview_summary(state)
            
            # Closing message
            closing = (
                "That concludes all my questions. Thank you so much for taking the time to interview with us today. "
                "I've prepared a summary of our conversation, and we'll be in touch with next steps soon. "
                "Is there anything else you'd like to add or any questions you have for me?"
            )
            
            print(f"\n[AI Interviewer]: {closing}")
            self.voice_interface.text_to_speech(closing, voice=AGENT_VOICE)
            
            # Wait for any final comments
            print("\n[System] Waiting for final candidate comments...")
            audio_path = self.voice_interface.record_audio()
            final_comments = self.voice_interface.transcribe_audio(audio_path)
            
            if final_comments:
                print(f"[Candidate]: {final_comments}")
                
                # Thank the candidate for their final comments
                thanks = "Thank you for sharing that. We'll definitely take it into consideration. Have a great day!"
                print(f"\n[AI Interviewer]: {thanks}")
                self.voice_interface.text_to_speech(thanks, voice=AGENT_VOICE)
            
            return {
                "interview_complete": True,
                "current_summary": summary
            }

    def process_answer(self, state: AgentState):
        """Process candidate's voice answer and evaluate with follow-up capability"""
        # Record audio answer using voice interface
        audio_path = self.voice_interface.record_audio()
        
        # Transcribe the audio answer
        candidate_answer = self.voice_interface.transcribe_audio(audio_path)
        print(f"[Candidate]: {candidate_answer}")
        
        # If no valid answer was detected, prompt again
        if not candidate_answer or len(candidate_answer.split()) < 3:
            retry_msg = "I'm sorry, I couldn't hear your response clearly. Could you please repeat your answer?"
            print(f"\n[AI Interviewer]: {retry_msg}")
            self.voice_interface.text_to_speech(retry_msg, voice=AGENT_VOICE)
            return {}  # No state change, will loop back to try again
        
        # Prepare conversation context
        conversation_context = "\n".join([
            f"Question {i+1}: {entry['question']}\nAnswer: {entry['answer']}" 
            for i, entry in enumerate(state['interview_log'])
        ])
        
        # Evaluate answer using LLM
        current_question = state['questions'][state['current_question_index'] - 1]
        evaluation_chain = ANSWER_EVALUATION_PROMPT | self.llm
        evaluation = evaluation_chain.invoke({
            "question": current_question,
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
            print(f"[System] Error parsing evaluation: {e}")
            print(f"[System] Raw evaluation: {evaluation}")
            acknowledgment = "Thank you for your answer."
            needs_follow_up = False
            follow_up = ""
            score_increment = 0
        
        # Short pause before responding (more natural)
        time.sleep(0.5)
        
        print(f"\n[AI Interviewer]: {acknowledgment}")
        self.voice_interface.text_to_speech(acknowledgment, voice=AGENT_VOICE)
        
        # Update interview log
        updated_log = state['interview_log'] + [{
            "question": current_question,
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
        
        # Short pause before asking follow-up (more natural)
        time.sleep(0.5)
        
        # Speak the follow-up question
        print(f"\n[AI Interviewer]: {follow_up}")
        self.voice_interface.text_to_speech(follow_up, voice=AGENT_VOICE)
        
        # Reset the needs_follow_up flag
        return {"needs_follow_up": False}

    def generate_interview_summary(self, state: AgentState):
        """Generate a summary of the interview"""
        try:
            # Prepare the interview log in a readable format
            formatted_log = []
            for i, entry in enumerate(state['interview_log']):
                formatted_log.append(f"Question {i+1}: {entry['question']}")
                formatted_log.append(f"Answer: {entry['answer']}")
                if entry.get('follow_up'):
                    formatted_log.append(f"Follow-up: {entry['follow_up']}")
            
            interview_log_str = "\n".join(formatted_log)
            
            # Generate summary using the prompt
            summary_chain = INTERVIEW_SUMMARY_PROMPT | self.llm
            summary = summary_chain.invoke({
                "job_description": state['job_description'],
                "requirements": state['requirements'],
                "interview_log": interview_log_str,
                "score": state['candidate_score']
            }).content
            
            return summary
        except Exception as e:
            print(f"[System] Error generating summary: {e}")
            return "Interview summary could not be generated due to an error."

    def build_graph(self):
        """Build the interview agent workflow graph"""
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("start", lambda state: state)
        workflow.add_node("initialize", self.initialize_interview)
        workflow.add_node("extract_requirements", self.extract_requirements)
        workflow.add_node("generate_questions", self.generate_questions)
        workflow.add_node("ask_question", self.ask_question)
        workflow.add_node("process_answer", self.process_answer)
        workflow.add_node("handle_follow_up", self.handle_follow_up)

        # Set edges
        workflow.set_entry_point("start")
        workflow.add_edge("start", "initialize")
        workflow.add_edge("initialize", "extract_requirements")
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
        
        initial_state = {
            "job_description": job_description,
            "requirements": "",
            "questions": [],
            "interview_log": [],
            "current_question_index": 0,
            "candidate_score": 0.0,
            "interview_complete": False,
            "needs_follow_up": False,
            "in_meeting": self.in_meeting,
            "current_summary": None
        }
        
        print("\n[System] Starting the interview process...")
        print(f"[System] Loaded job description ({len(job_description.split())} words)")
        
        # Execute the interview workflow graph
        result = self.graph.invoke(initial_state)
        
        # Return the final state
        return result