# src/utils/semantic_checker.py
import logging
from sentence_transformers import SentenceTransformer, util
import torch

# --- Setup a dedicated logger for this module ---
logger = logging.getLogger(__name__)

# --- Load the model only ONCE when the app starts for efficiency ----
try:
    # 'all-MiniLM-L6-v2' is a great choice: fast, lightweight, and high-quality.
    MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("SentenceTransformer model ('all-MiniLM-L6-v2') loaded successfully.")
except Exception as e:
    logger.error("Failed to load SentenceTransformer model: %s", e, exc_info=True)
    MODEL = None

def calculate_similarity(user_answer: str, reference_answer: str) -> float:
    """
    Calculates the semantic similarity between two texts and scales it to a 0-5 score.

    Args:
        user_answer (str): The user's provided answer.
        reference_answer (str): The ideal or "golden" reference answer.

    Returns:
        float: A similarity score between 0.0 and 5.0.
    """
    if MODEL is None:
        logger.critical("Semantic checker model is not available. Returning score of 0.")
        return 0.0

    try:
        # 1. Generate embeddings for both answers
        # convert_to_tensor=True is important for performance
        embedding1 = MODEL.encode(user_answer, convert_to_tensor=True)
        embedding2 = MODEL.encode(reference_answer, convert_to_tensor=True)

        # 2. Compute cosine similarity
        cosine_scores = util.cos_sim(embedding1, embedding2)
        
        # 3. Scale the score from [-1, 1] range to [0, 5] range
        # The cosine similarity score is originally between -1 and 1.
        # Normalize it to a [0, 1] range: (score + 1) / 2
        # Then multiply by 5 to match the rubric's scale.
        similarity_score = cosine_scores.item()
        score_out_of_5 = ((similarity_score + 1) / 2) * 5

        # Cap the score to a max of 5.0 to handle any floating point inaccuracies
        return min(score_out_of_5, 5.0)

    except Exception as e:
        logger.error("Error during similarity calculation: %s", e, exc_info=True)

        return 0.0
