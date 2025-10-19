# src/utils/rag_retriever.py
import yaml
import os
import random
import logging

# --- Setup a dedicated logger for this module ----
logger = logging.getLogger(__name__)

class QuestionRetriever:
    def __init__(self, bank_path=None):
        """
        Initializes the retriever by loading the question bank from a YAML file.
        """
        self.question_bank = []
        
        # FIX: Better path resolution for Hugging Face Spaces
        if bank_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            bank_path = os.path.join(current_dir, "question_bank.yml")
        
        logger.info(f"Attempting to load question bank from: {bank_path}")
        
        try:
            with open(bank_path, 'r') as f:
                self.question_bank = yaml.safe_load(f)
            
            # Check if loading was successful and yielded a list
            if isinstance(self.question_bank, list):
                logger.info(f"✅ Successfully loaded {len(self.question_bank)} questions from the bank.")
            else:
                logger.error(f"❌ Failed to load question bank: YAML file at {bank_path} did not parse as a list. Got type: {type(self.question_bank)}")
                self.question_bank = []
                
        except FileNotFoundError:
            logger.error(f"❌ Question bank file not found at path: {bank_path}")
            # Try alternative path for Hugging Face Spaces
            alternative_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils", "question_bank.yml")
            logger.info(f"Trying alternative path: {alternative_path}")
            try:
                with open(alternative_path, 'r') as f:
                    self.question_bank = yaml.safe_load(f)
                if isinstance(self.question_bank, list):
                    logger.info(f"✅ Successfully loaded {len(self.question_bank)} questions from alternative path.")
                else:
                    self.question_bank = []
            except Exception as e2:
                logger.error(f"❌ Failed to load from alternative path: {e2}")
                
        except yaml.YAMLError as e:
            logger.error(f"❌ Error parsing YAML in question bank: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error loading question bank: {e}", exc_info=True)

    def retrieve(self, skills: list, num_technical: int = 3, num_behavioral: int = 3) -> list:
        """
        Retrieves a set of questions by filtering based on a list of skills.
        
        Args:
            skills (list): A list of skills extracted from the resume (e.g., ['SQL', 'Python']).
            num_technical (int): The number of technical questions to retrieve.
            num_behavioral (int): The number of behavioral questions to retrieve.

        Returns:
            list: A list of question dictionaries that match the criteria.
        """
        if not self.question_bank:
            logger.warning("⚠️ Attempted to retrieve questions, but the question bank is empty.")
            return []

        if not skills:
            logger.warning("⚠️ No skills provided for question retrieval.")
            return []

        # Normalize skills for case-insensitive matching
        resume_skills = set(s.lower() for s in skills if isinstance(s, str))
        
        # Filter questions where the question's skill is in the resume's skills
        relevant_questions = [
            q for q in self.question_bank 
            if isinstance(q, dict) and q.get('skill', '').lower() in resume_skills
        ]

        # Separate by type
        tech_questions = [q for q in relevant_questions if q.get('type') == 'Technical']
        behav_questions = [q for q in relevant_questions if q.get('type') == 'Behavioral']

        logger.info(f"Found {len(tech_questions)} technical and {len(behav_questions)} behavioral questions matching skills: {skills}")

        # Randomly sample the desired number of questions safely
        final_tech = []
        final_behav = []
        
        if tech_questions:
            final_tech = random.sample(tech_questions, min(len(tech_questions), num_technical))  # FIXED: removed extra parenthesis
        else:
            logger.warning("No technical questions found for the given skills.")
            
        if behav_questions:
            final_behav = random.sample(behav_questions, min(len(behav_questions), num_behavioral))  # FIXED: removed extra parenthesis
        else:
            logger.warning("No behavioral questions found for the given skills.")
        
        return result

# --- Test function for debugging ---
def test_retriever():
    """Test function to verify the retriever works"""
    print("🧪 Testing QuestionRetriever...")
    retriever = QuestionRetriever()
    print(f"Question bank size: {len(retriever.question_bank)}")
    
    # Test with sample skills
    test_skills = ['Python', 'SQL']
    questions = retriever.retrieve(test_skills, num_technical=2, num_behavioral=1)
    print(f"Retrieved {len(questions)} questions for skills: {test_skills}")
    
    for i, q in enumerate(questions):
        print(f"{i+1}. {q.get('question')} [{q.get('type')}]")

if __name__ == "__main__":
    test_retriever()
