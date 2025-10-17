import google.generativeai as genai
import os
import re
from tenacity import retry, stop_after_attempt, wait_exponential

# --- Import project-specific modules ---
try:
    from .evaluation_prompts import EVALUATION_PROMPT_TEMPLATE
    from .audit_logger import audit_log
except ImportError:
    # Handle case where script is run directly for testing
    from evaluation_prompts import EVALUATION_PROMPT_TEMPLATE
    from audit_logger import audit_log

# --- Securely configure the Gemini client from environment variables ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    error_msg = "GEMINI_API_KEY environment variable not found. Please set it in Hugging Face Spaces secrets."
    print(f"❌ {error_msg}")
    # Get all environment variables for debugging (don't print values for security)
    env_vars = [key for key in os.environ.keys() if 'KEY' in key or 'SECRET' in key]
    print(f"🔍 Found these relevant environment variables: {env_vars}")
    raise ValueError(error_msg)

try:
    genai.configure(api_key=api_key)
    print("✅ Gemini API configured successfully")
except Exception as e:
    print(f"❌ Error configuring Gemini API: {e}")
    raise

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def get_gemini_response(prompt: str) -> str | None:
    """
    Sends a prompt to the Gemini API and returns the response text.
    Includes structured auditing.
    """
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text

        # Log the transaction after receiving the response
        audit_log.info("Gemini General Call", extra={
            'model_name': 'gemini-1.5-flash',
            'prompt_sent': prompt[:500] + "..." if len(prompt) > 500 else prompt,  # Truncate long prompts
            'response_received': response_text[:500] + "..." if len(response_text) > 500 else response_text
        })
        return response_text
    except Exception as e:
        print(f"❌ Error calling Gemini API in get_gemini_response: {e}")
        return None

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def generate_reference_answer(question: str, resume_context: str) -> str:
    """Generates an ideal reference answer for a given question."""
    prompt = f"""
    As a senior technical interviewer, provide an ideal, textbook-quality answer for the following interview question.
    The answer should be tailored to the candidate's resume for context.
    Use the STAR method for behavioral questions. Be clear and concise.

    QUESTION: "{question}"
    
    CANDIDATE'S RESUME CONTEXT:
    ---
    {resume_context}
    ---
    
    IDEAL ANSWER:
    """
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text

        audit_log.info("Gemini Reference Answer Call", extra={
            'model_name': 'gemini-1.5-flash',
            'prompt_sent': prompt[:500] + "..." if len(prompt) > 500 else prompt,
            'response_received': response_text[:500] + "..." if len(response_text) > 500 else response_text
        })
        return response_text
    except Exception as e:
        print(f"❌ Error generating reference answer: {e}")
        return "Could not generate a reference answer."

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def evaluate_with_rubric(question: str, user_answer: str, resume_context: str) -> tuple[str, float]:
    """
    Evaluates an answer using the detailed LLM rubric, extracts the score,
    and logs the transaction.
    Returns both the full text feedback and the numerical score.
    """
    prompt = EVALUATION_PROMPT_TEMPLATE.format(
        question=question,
        user_answer=user_answer,
        resume_context=resume_context
    )
    
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        generation_config = genai.types.GenerationConfig(
            temperature=0.2  # Low temperature for deterministic output
        )
        
        response = model.generate_content(prompt, generation_config=generation_config)
        full_feedback_text = response.text
        
        # Use regex to find "Overall Score: [score]/5"
        score_match = re.search(r"Overall Score:\s*([0-9.]+)\s*/\s*5", full_feedback_text, re.IGNORECASE)
        
        llm_score = 0.0
        if score_match:
            llm_score = float(score_match.group(1))
        else:
            print("⚠️ Warning: Could not parse Overall Score from LLM feedback.")

        audit_log.info("Gemini Evaluation Call", extra={
            'model_name': 'gemini-1.5-flash',
            'temperature': 0.2,
            'prompt_sent': prompt[:500] + "..." if len(prompt) > 500 else prompt,
            'response_received': full_feedback_text[:500] + "..." if len(full_feedback_text) > 500 else full_feedback_text,
            'parsed_score': llm_score
        })
            
        return full_feedback_text, llm_score

    except Exception as e:
        print(f"❌ Error in rubric evaluation: {e}")
        return f"Evaluation error: {str(e)}", 0.0