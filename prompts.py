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

ANSWER_EVALUATION_PROMPT = PromptTemplate(
    input_variables=["question", "answer", "context"],
    template="""You are an expert technical interviewer evaluating a candidate's response.

Previous Interview Context:
{context}

Current Question: {question}
Candidate's Answer: {answer}

Evaluate the answer comprehensively:
1. Technical Accuracy: How well does the answer demonstrate technical knowledge?
2. Depth of Understanding: Does the candidate show deep insight or just surface-level knowledge?
3. Communication Skills: Is the answer clear, structured, and articulate?
4. Problem-Solving Approach: How does the candidate explain their thought process?

Provide a structured evaluation with:
- A brief assessment of the answer
- Strengths of the response
- Areas for improvement
- A numerical score between 0-10 representing the candidate's performance

Response Format (MUST BE VALID JSON):
{{
    "assessment": "...",
    "strengths": ["...", "..."],
    "improvements": ["...", "..."],
    "score": X.X
}}
"""
)