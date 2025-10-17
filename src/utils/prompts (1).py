# src/utils/prompts.py

# Notice the change in the instructions and the description of the input
QUESTION_PROMPT_TEMPLATE = """You are an expert technical interviewer for elite tech companies.
Your task is to generate highly specific interview questions based on a candidate's structured resume data.

Below is the candidate's structured resume data in JSON format:
----------------------------
{resume_text}
----------------------------

The candidate is applying for this role: {target_role}

Generate 3 behavioral questions and 3 technical questions specifically tailored to this candidate's resume.

Guidelines:
1. For behavioral questions, ask about specific projects or experiences linked to the ORGANIZATIONS listed.
2. For technical questions, directly reference the SKILLS listed in the JSON. For example, if "PyTorch" is a skill, ask a specific PyTorch question.
3. The questions should be challenging, designed to probe the depth of their experience with the listed skills and roles.

Please output the questions in this exact format:
BEHAVIORAL QUESTIONS:
1. [Question 1]
2. [Question 2]
3. [Question 3]

TECHNICAL QUESTIONS:
1. [Question 1]
2. [Question 2]
3. [Question 3]
"""
REWRAP_PROMPT_TEMPLATE = """You are an expert technical interviewer at a top tech company.
Your task is to rewrite a given set of standard interview questions to be highly specific and personalized to the candidate's resume.

CANDIDATE'S RESUME (Structured JSON):
----------------------------
{resume_context}
----------------------------

STANDARD QUESTIONS TO PERSONALIZE:
----------------------------
{retrieved_questions}
----------------------------

Please rewrite and tailor each of the standard questions. Ground your new questions in the candidate's specific projects, experiences, and skills listed in their resume JSON.

For example, if the standard question is "Tell me about a challenging project" and the resume mentions a "customer churn prediction model using PyTorch," a good rewritten question would be: "In your project on customer churn prediction, what were the most significant technical challenges you faced while implementing the PyTorch model?"

Output the rewritten questions in the same format as before:
BEHAVIORAL QUESTIONS:
1. [Rewritten Question 1]
...

TECHNICAL QUESTIONS:
1. [Rewritten Question 1]
...
"""
ROLE_ONLY_PROMPT_TEMPLATE = """You are an expert technical interviewer for tech companies.
Your task is to generate challenging and insightful interview questions for a specific job role.

The candidate is applying for this role: {target_role}

Generate 3 behavioral questions and 3 technical questions that are highly relevant for this role. The questions should be general enough to not require a resume, but specific enough to effectively test a candidate's qualifications for the position.

Please output the questions in this exact format:
BEHAVIORAL QUESTIONS:
1. [Question 1]
2. [Question 2]
3. [Question 3]

TECHNICAL QUESTIONS:
1. [Question 1]
2. [Question 2]
3. [Question 3]
"""