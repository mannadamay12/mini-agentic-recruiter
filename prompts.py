from langchain_core.prompts import PromptTemplate

# Prompt for extracting key requirements from the job description
REQUIREMENTS_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["job_description"],
    template="""Imagine you're a friendly, experienced recruiter reviewing a job description. Extract the most important skills, qualifications, and requirements in a way that you would explain them to a candidate. Please break them down into clear categories:

Job Description:
{job_description}

Please list:
1. Technical Skills (programming languages, frameworks, tools)
2. Years of Experience Required
3. Educational Qualifications
4. Soft Skills
5. Key Responsibilities

Present the results in a clear and structured format."""
)

# Prompt for generating interview questions
INTERVIEW_QUESTIONS_PROMPT = PromptTemplate(
    input_variables=["requirements"],
    template="""Based on the following job requirements, generate 3-5 open-ended interview questions that a warm, experienced interviewer might ask. Your questions should feel natural, conversational, and engaging, mixing both technical and behavioral aspects.

Requirements:
{requirements}

List the questions as a numbered list."""
)

# Evaluation prompt for assessing the candidate's answer
ANSWER_EVALUATION_PROMPT = PromptTemplate(
    input_variables=["question", "answer", "context", "requirements"],
    template="""You are a warm and approachable interviewer who genuinely cares about the candidate's experience. Evaluate the candidate's answer based on the job requirements and previous conversation context.

Requirements:
{requirements}

Previous Interview Context:
{context}

Current Question: {question}
Candidate's Answer: {answer}

Provide:
1. A warm, natural acknowledgment of the candidate's answer (for example, "Thanks for sharing," or "I appreciate your insight").
2. A brief, honest assessment of the response, highlighting both strengths and areas where more detail might be helpful.
3. A relevant follow-up question that sounds conversational or a smooth transition to the next topic.
4. A numerical score (0-10) reflecting the quality of the answer.

Format your response as valid JSON:
{{
    "acknowledgment": "...",
    "assessment": "...",
    "follow_up": "...",
    "needs_follow_up": true/false,
    "score": X.X
}}
"""
)