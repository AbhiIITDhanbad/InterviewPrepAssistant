# src/utils/report_generator.py
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch

# --- Setup a dedicated logger for this module ---
logger = logging.getLogger(__name__)

# --- Helper function to draw wrapped text and manage layout flow ---
def draw_section(c, x, y, width, title, content, styles):
    """
    Draws a section with a title and wrapped content.
    Returns the y-coordinate for the start of the next section.
    """
    # Draw the title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, title)
    y -= 0.25 * inch

    # Create a Paragraph object for automatic text wrapping
    p = Paragraph(content, styles["Normal"])
    p_width, p_height = p.wrapOn(c, width, y)
    
    # Draw the paragraph
    p.drawOn(c, x, y - p_height)
    
    # Return the new y-coordinate below this paragraph
    return y - p_height - 0.4 * inch


def create_pdf_report(file_path: str, report_data: dict):
    """
    Generates a professional, dynamically laid-out PDF report.
    
    Args:
        file_path (str): The path to save the PDF.
        report_data (dict): A dictionary containing all data for the report.
    """
    try:
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        
        # Define margins
        margin = 1 * inch
        content_width = width - 2 * margin

        # Get standard styles
        styles = getSampleStyleSheet()

        # --- Report Header ---
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width / 2.0, height - 0.75 * inch, "Interview Preparation Report")
        
        # --- Start drawing content below the header ---
        # y_cursor tracks the current vertical position on the page
        y_cursor = height - 1.5 * inch

        # --- Summary Score Section ---
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, y_cursor, "Performance Summary")
        y_cursor -= 0.25 * inch
        
        c.setFont("Helvetica", 12)
        score_text = (
            f"Final Weighted Score: {report_data.get('final_score', 'N/A'):.2f} / 5.0 | "
            f"AI Rubric Score: {report_data.get('rubric_score', 'N/A'):.2f} / 5.0 | "
            f"Semantic Score: {report_data.get('semantic_score', 'N/A'):.2f} / 5.0"
        )
        c.drawString(margin, y_cursor, score_text)
        y_cursor -= 0.5 * inch

        # --- Dynamic Sections using the helper function ---
        y_cursor = draw_section(c, margin, y_cursor, content_width, 
                                "✅ Key Strengths:", 
                                report_data.get('strengths', 'No specific strengths identified.'), 
                                styles)

        y_cursor = draw_section(c, margin, y_cursor, content_width,
                                "📈 Areas for Improvement:",
                                report_data.get('areas_for_improvement', 'No specific areas for improvement identified.'),
                                styles)
                                
        y_cursor = draw_section(c, margin, y_cursor, content_width,
                                "🎯 Your Plan for Next Week:",
                                report_data.get('next_plan', 'Focus on practicing the areas for improvement.'),
                                styles)
        
        # --- Add a separator line ---
        c.line(margin, y_cursor, width - margin, y_cursor)
        y_cursor -= 0.4 * inch

        # --- Detailed Q&A Section ---
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, y_cursor, "Detailed Evaluation")
        y_cursor -= 0.25 * inch

        for i, qa in enumerate(report_data.get('qa_pairs', [])):
            # Check if there is enough space for the next Q&A, otherwise start a new page
            if y_cursor < 2 * inch:
                c.showPage() # Create a new page
                y_cursor = height - margin # Reset y_cursor

            y_cursor = draw_section(c, margin, y_cursor, content_width,
                                    f"Question {i+1}:",
                                    qa.get('question', 'N/A'),
                                    styles)
            y_cursor = draw_section(c, margin, y_cursor, content_width,
                                    "Your Answer:",
                                    qa.get('answer', 'N/A'),
                                    styles)

        c.save()
        logger.info(f"Successfully generated PDF report at {file_path}")

    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}", exc_info=True)