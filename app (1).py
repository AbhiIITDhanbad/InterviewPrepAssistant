# app.py
import os
import sys
import logging

# --- 1. Add the 'src' directory to the Python path ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

# --- 2. Configure Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info(f"Current directory: {current_dir}")

# --- 3. Import the UI creation function from your main app file ---
try:
    from gradio_app import create_interface
    logger.info("✅ Successfully imported 'create_interface' from gradio_app")
except ImportError as e:
    logger.critical(f"❌ Could not import gradio_app: {e}")
    sys.exit(1)

# --- 4. Create and launch the Gradio interface ---
logger.info("Creating the Gradio interface...")
demo = create_interface()

if __name__ == "__main__":
    logger.info("🚀 Launching the Your AI Interview Assistant...")
    # Simple launch without share parameter for Hugging Face Spaces
    demo.launch()