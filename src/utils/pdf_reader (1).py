import fitz  # PyMuPDF library, which is more robust for complex layouts
import logging
import os

# --- Setup a dedicated logger for this module ---
# This is better than print() for production applications
logger = logging.getLogger(__name__)

def read_pdf(file_path: str) -> str | None:
    """
    Extracts text from a PDF file using the PyMuPDF library for superior accuracy
    with modern resume formats (e.g., columns, tables).

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        str | None: All extracted text, or None if an error occurs.
    """
    # --- ADDED: Specific check for file existence ---
    if not os.path.exists(file_path):
        logger.error(f"File not found at path: {file_path}")
        return None

    text = ""
    try:
        # Open the PDF file using PyMuPDF (fitz)
        with fitz.open(file_path) as doc:
            logger.info(f"Successfully opened PDF: {file_path}")
            # Loop through each page and extract text, preserving layout
            for page in doc:
                text += page.get_text() + "\n"
        return text
    except Exception as e:
        # Catches PyMuPDF-specific errors or other unexpected issues
        logger.error(f"Failed to read or parse PDF '{file_path}'. Reason: {e}", exc_info=True)
        return None

# --- Local Testing Block ---
if __name__ == "__main__":
    # This block now uses a relative path, making it portable.
    # It assumes you have a 'sample_data' directory at the project root
    # with a resume inside for testing.
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sample_file_path = os.path.join(PROJECT_ROOT, "sample_data", "sample_resume.pdf")

    # Configure basic logging to see output in the console for the test
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    print(f"--- Testing PDF Reader on '{sample_file_path}' ---")
    if os.path.exists(sample_file_path):
        sample_text = read_pdf(sample_file_path)
        if sample_text:
            print("\n✅ PDF read successfully! First 500 characters:")
            print(sample_text[:500])
        else:
            print("\n❌ Failed to read PDF. Check logs for details.")
    else:
        print(f"\n⚠️ Test skipped: Please add a PDF file at '{sample_file_path}' to run this local test.")