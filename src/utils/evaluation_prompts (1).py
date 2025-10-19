# src/utils/evaluation_prompts.py

EVALUATION_PROMPT_TEMPLATE = """
You are an experienced interview coach. Evaluate the following interview answer based on these criteria:

**QUESTION:** {question}

**USER'S ANSWER:** {user_answer}

**RESUME CONTEXT:** {resume_context}

**EVALUATION CRITERIA:**
1. **STAR Method (Situation, Task, Action, Result):** Does the answer follow this structure?
2. **Relevance:** Does the answer directly address the question and use examples from the resume?
3. **Clarity:** Is the answer concise and easy to understand?
4. **Technical Accuracy** (for technical questions): Is the information correct?
5. **Impact:** Does the answer demonstrate meaningful results or learning?

**Please provide evaluation in this exact format:**
- STAR Score: [score]/5
- Relevance Score: [score]/5  
- Clarity Score: [score]/5
- Technical Accuracy: [score]/5 (if technical) or N/A
- Impact Score: [score]/5
- Overall Score: [average]/5

**Detailed Feedback:**
[Your constructive feedback here]

**Improved Answer Example:**
[Provide a better version of the answer]
"""
