import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("No OpenAI API key found. Please set OPENAI_API_KEY in .env file.")

# Agent Configuration
MAX_INTERVIEW_QUESTIONS = 3
INTERVIEW_LANGUAGE_MODEL = 'gpt-3.5-turbo'