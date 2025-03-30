from langchain_core.prompts import PromptTemplate

# Prompt for extracting key requirements from job description
REQUIREMENTS_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["job_description"],
    template="""Analyze the following job description and extract the most critical skills, 
    qualifications, and requirements:

Job Description:
{job_description}

Extract and categorize:
1. Technical Skills (programming languages, frameworks, tools)
2. Years of Experience Required
3. Educational Qualifications
4. Soft Skills
5. Key Responsibilities

Output the results in a clear, structured format."""
)

# Prompt for generating interview questions
INTERVIEW_QUESTIONS_PROMPT = PromptTemplate(
    input_variables=["requirements"],
    template="""Based on the following job requirements, generate 3-5 open-ended interview 
    questions that will help assess a candidate's suitability:

Requirements:
{requirements}

Guidelines for Questions:
- Create questions that probe deeper than surface-level answers
- Mix technical and behavioral questions
- Ensure questions relate directly to the job requirements
- Make questions engaging and encourage detailed responses

Output the questions as a numbered list."""
)

# Modified evaluation prompt in prompts.py
ANSWER_EVALUATION_PROMPT = PromptTemplate(
    input_variables=["question", "answer", "context", "requirements"],
    template="""You are an expert technical interviewer evaluating a candidate's response.

Requirements:
{requirements}

Previous Interview Context:
{context}

Current Question: {question}
Candidate's Answer: {answer}

Provide:
1. A natural acknowledgment of the candidate's answer
2. A brief assessment of the response quality
3. A relevant follow-up question OR a transition to the next topic
4. A numerical score (0-10)

Response Format (MUST BE VALID JSON):
{{
    "acknowledgment": "...",
    "assessment": "...",
    "follow_up": "...",
    "needs_follow_up": true/false,
    "score": X.X
}}
"""
)