# src/gradio_app.py
import gradio as gr
import os
import sys
import json
import datetime
import tempfile
import re
import logging
from pdf2image import convert_from_path # For resume preview

# --- Setup Professional Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Add project root to Python path ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# --- Import your utility functions ---
# --- Import your utility functions ---
# --- Import your utility functions ---
try:
    from utils.pdf_reader import read_pdf
    from utils.resume_parser import parse_resume_text
    from utils.gemini_client import get_gemini_response, evaluate_with_rubric, generate_reference_answer
    from utils.prompts import REWRAP_PROMPT_TEMPLATE, ROLE_ONLY_PROMPT_TEMPLATE
    from utils.rag_retreiver import QuestionRetriever
    from utils.semantic_checker import calculate_similarity
    from utils.report_generator import create_pdf_report
    logger.info("✅ All utility modules imported successfully.")
except ImportError as e:
    logger.critical(f"FATAL: Error importing modules: {e}. The application cannot start. Please check file paths and dependencies.")
    # Try to provide more detailed error information
    import traceback
    logger.critical(traceback.format_exc())
    sys.exit(1)
# --- Session State and Global Variables ---
session_state = {
    "generated_questions": "",
    "evaluation_history": [] # Stores full evaluation details for the report
}
retriever = QuestionRetriever()

# --- FIX: Dynamically load job categories from the taxonomy file ---
def load_job_categories():
    taxonomy_path = os.path.join(PROJECT_ROOT, "src", "utils", "skill_taxonomy.json")
    try:
        with open(taxonomy_path, 'r') as f:
            return list(json.load(f).keys())
    except Exception as e:
        logger.error(f"Could not load job categories from JSON: {e}")
        return ["Data Science", "Backend Development", "Frontend Development", "Cloud & DevOps"] # Fallback

JOB_CATEGORIES = load_job_categories()


# --- Helper Functions ---
def create_resume_preview(pdf_path):
    """Generates a PNG preview of the first page of a PDF."""
    try:
        # dpi reduced for faster preview generation
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
        if images:
            preview_path = os.path.join(tempfile.gettempdir(), f"resume_preview_{os.path.basename(pdf_path)}.png")
            images[0].save(preview_path)
            return preview_path
    except Exception as e:
        logger.error(f"Could not create resume preview: {e}")
    return None

def download_questions_text():
    """Saves generated questions to a temporary text file for download."""
    questions = session_state.get("generated_questions", "No questions generated yet.")
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding='utf-8') as f:
        f.write(questions)
        return f.name

# --- Core Application Logic (Generator Functions for Streaming UI Updates) ---
def generate_questions_gradio(resume_file, target_role, job_category):
    """
    Main function for the question generation workflow.
    Yields status updates and final outputs to the Gradio interface.
    """
    if not resume_file and (not target_role or not target_role.strip()):
        gr.Warning("Please upload a resume or enter a target role.")
        return "Status: Idle", "", None, None

    # Clear previous state
    session_state["generated_questions"] = ""

    if resume_file is None:
        # COLD START PATH
        yield "⏳ Generating general questions for the role...", "", None, None
        prompt = ROLE_ONLY_PROMPT_TEMPLATE.format(target_role=target_role.strip())
        questions = get_gemini_response(prompt)
        if not questions:
            gr.Error("Failed to generate questions. Please check API key and logs.")
            yield "❌ Failed to generate questions.", "", None, None
        else:
            session_state["generated_questions"] = questions
            yield "✅ General questions generated!", questions, None, None
    else:
        # RESUME-BASED RAG PATH
        try:
            file_path = resume_file.name
            yield "⏳ 1/4: Reading resume...", "", None, None
            raw_text = read_pdf(file_path)
            if not raw_text:
                gr.Error("Failed to read the uploaded PDF.")
                yield "❌ Failed to read PDF.", "", None, None
                return

            yield "⏳ 2/4: Analyzing resume skills...", "", None, None
            structured_resume_str = parse_resume_text(raw_text, job_category)
            structured_resume_dict = json.loads(structured_resume_str)
            resume_skills = structured_resume_dict.get("SKILLS", [])
            preview_path = create_resume_preview(file_path)

            yield "⏳ 3/4: Retrieving questions from bank...", "", preview_path, structured_resume_dict
            if not resume_skills:
                gr.Warning("No specific skills found. Falling back to general role-based questions.")
                prompt = ROLE_ONLY_PROMPT_TEMPLATE.format(target_role=target_role.strip())
            else:
                retrieved_questions = retriever.retrieve(skills=resume_skills)
                if not retrieved_questions:
                    gr.Warning("No questions found in bank for your specific skills. Falling back to general questions.")
                    prompt = ROLE_ONLY_PROMPT_TEMPLATE.format(target_role=target_role.strip())
                else:
                    prompt = REWRAP_PROMPT_TEMPLATE.format(
                        resume_context=structured_resume_str,
                        retrieved_questions=str(retrieved_questions)
                    )

            yield "⏳ 4/4: Personalizing questions with AI...", "", preview_path, structured_resume_dict
            final_questions = get_gemini_response(prompt)
            session_state["generated_questions"] = final_questions

            yield "✅ Questions generated successfully!", final_questions, preview_path, structured_resume_dict
        except Exception as e:
            logger.error("Error in question generation pipeline: %s", e, exc_info=True)
            gr.Error(f"An unexpected error occurred: {e}")
            yield f"❌ Error: {e}", "", None, None


def evaluate_single_answer(question, user_answer, resume_file):
    """
    Main function for the hybrid evaluation workflow.
    Yields status updates and the final report.
    """
    if not all([question, user_answer, resume_file]):
        gr.Warning("Please provide the question, your answer, and upload your resume for evaluation.")
        return "Status: Missing inputs.", ""
    try:
        resume_text = read_pdf(resume_file.name)
        if not resume_text:
            gr.Error("Failed to read resume for context.")
            return "❌ Failed to read resume.", ""

        yield "⏳ 1/3: Generating ideal reference answer...", ""
        reference_answer = generate_reference_answer(question, resume_text)

        yield "⏳ 2/3: Evaluating answer with AI rubric...", ""
        llm_feedback_text, llm_rubric_score = evaluate_with_rubric(question, user_answer, resume_text)

        yield "⏳ 3/3: Calculating semantic similarity...", ""
        semantic_score = calculate_similarity(user_answer, reference_answer)

        final_score = (0.6 * llm_rubric_score) + (0.4 * semantic_score)

        final_report = f"""
        ## Hybrid Evaluation Report
        - **Final Weighted Score:** `{final_score:.2f} / 5.0`
        - **AI Rubric Score:** `{llm_rubric_score:.2f} / 5.0`
        - **Semantic Similarity Score:** `{semantic_score:.2f} / 5.0` (how closely your answer matches an ideal one)
        ---
        ### AI Coach's Detailed Feedback:
        {llm_feedback_text}
        """
        # Store for report download
        session_state["evaluation_history"].append({
            "question": question,
            "answer": user_answer,
            "feedback": llm_feedback_text, # Store the raw feedback for parsing
            "final_score": final_score,
            "rubric_score": llm_rubric_score,
            "semantic_score": semantic_score
        })
        yield "✅ Evaluation complete!", final_report

    except Exception as e:
        logger.error("Error during evaluation pipeline: %s", e, exc_info=True)
        gr.Error(f"An evaluation error occurred: {e}")
        yield f"❌ Error: {e}", ""

def generate_and_download_report():
    """Gathers session data and creates a downloadable PDF report."""
    if not session_state["evaluation_history"]:
        gr.Warning("No evaluations to report. Please evaluate at least one answer first.")
        return None
    
    # --- FIX: Smarter report data aggregation ---
    # A simple example of extracting strengths/weaknesses from feedback text
    strengths = []
    improvements = []
    for eval_item in session_state["evaluation_history"]:
        # This parsing can be made more robust with regex or an LLM call
        if "strength" in eval_item["feedback"].lower():
            strengths.append(eval_item["question"])
        if "improve" in eval_item["feedback"].lower():
            improvements.append(eval_item["question"])

    report_data = {
        "qa_pairs": session_state["evaluation_history"],
        "strengths": "Demonstrated strong STAR method usage in questions about: " + ", ".join(strengths),
        "areas_for_improvement": "Could improve technical depth in answers to questions about: " + ", ".join(improvements),
        "next_plan": "Review core concepts related to the improvement areas. Practice mock interviews focusing on concise, impactful answers.",
        "final_score": session_state["evaluation_history"][-1]['final_score'],
        "rubric_score": session_state["evaluation_history"][-1]['rubric_score'],
        "semantic_score": session_state["evaluation_history"][-1]['semantic_score']
    }
    
    report_path = os.path.join(tempfile.gettempdir(), "Interview_Prep_Report.pdf")
    create_pdf_report(report_path, report_data)
    return report_path


# --- Gradio UI Definition ---
def create_interface():
    with gr.Blocks(theme=gr.themes.Soft(), title="Interview_Prep Assistant") as demo:
        gr.Markdown("# 🎯InterviewPrep Assistant")
        gr.Markdown("Your personal AI coach to prepare for top-tier technical interviews")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 1. Your Details")
                resume_upload = gr.File(
                    label="📄 Upload Resume (Optional for general questions)",
                    file_types=[".pdf"],
                )
                target_role_input = gr.Textbox(
                    label="🎯 Target Role",
                    placeholder="e.g., Senior Machine Learning Engineer @ Google",
                )
                job_category_input = gr.Dropdown(
                    label="👨‍💻 Job Category (for skill analysis)",
                    choices=JOB_CATEGORIES,
                    value=JOB_CATEGORIES[0] if JOB_CATEGORIES else ""
                )
                
            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.TabItem("🤔 Generate Questions"):
                        gr.Markdown("### 2. Get Personalized Questions")
                        gen_q_btn = gr.Button("Generate Questions 🚀", variant="primary")
                        status_output = gr.Textbox(label="Status", interactive=False)
                        questions_output = gr.Textbox(label="💡 Your Tailored Interview Questions", lines=10, interactive=False)
                        download_q_btn = gr.Button("📥 Download Questions (.txt)")
                        download_q_file = gr.File(label="Download Questions", interactive=False)

                    with gr.TabItem("📝 Evaluate Your Answers"):
                        gr.Markdown("### 2. Get Expert Feedback")
                        question_input = gr.Textbox(label="📋 Paste an interview question here", lines=3)
                        answer_input = gr.Textbox(label="💬 Write your answer here", lines=6)
                        eval_btn = gr.Button("Evaluate Answer 📊", variant="primary")
                        eval_status = gr.Textbox(label="Status", interactive=False)
                        eval_output = gr.Markdown(label="📈 Your Detailed Evaluation Report")
                        download_report_btn = gr.Button("📥 Download Full Report (PDF)")
                        report_output_file = gr.File(label="Download Report", interactive=False)

        with gr.Accordion("🔍 Resume Analysis Preview", open=False):
            gr.Markdown("This panel shows the AI's understanding of your resume. The better the parsing, the better the questions!")
            with gr.Row():
                resume_preview_output = gr.Image(label="Resume Preview (First Page)", scale=1)
                parsed_summary_output = gr.JSON(label="Parsed Resume Data (Skills, Companies, etc.)", scale=2)

        # --- Event Listeners ---
        gen_q_btn.click(
            fn=generate_questions_gradio,
            inputs=[resume_upload, target_role_input, job_category_input],
            outputs=[status_output, questions_output, resume_preview_output, parsed_summary_output]
        )
        download_q_btn.click(fn=download_questions_text, outputs=[download_q_file])
        eval_btn.click(
            fn=evaluate_single_answer,
            inputs=[question_input, answer_input, resume_upload],
            outputs=[eval_status, eval_output]
        )
        download_report_btn.click(fn=generate_and_download_report, outputs=[report_output_file])

    return demo

if __name__ == "__main__":
    # Configure logging for the main app...w
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Starting MAANG-Ready Interview Assistant...")
    app = create_interface()
    app.launch(share=True)
