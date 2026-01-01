# 🎯 InterviewPrep Assistant

An AI-powered interview coach that generates personalized questions from your resume and provides in-depth, hybrid evaluations of your answers. Built with Google's Gemini 1.5 Flash, spaCy, and a custom RAG (Retrieval-Augmented Generation) pipeline.
## Project Demo: https://drive.google.com/file/d/1-z1w5WeHih1dPtDtXrqvi380MDgqT1ZK/view?usp=sharing

## ✨ Key Features

* **📄 NLP-Powered Resume Parsing:** Leverages `spaCy` and a custom `skill_taxonomy.json` to intelligently parse your resume. It redacts PII (emails, phone numbers) and extracts key entities like `SKILLS`, `ORG` (Organizations), and `LOCATIONS`.
* **🧠 Personalized Question Generation (RAG):** Upload your resume and target role. The app uses your extracted `SKILLS` to retrieve relevant questions from a curated question bank (`question_bank.yml`). These are then personalized by Gemini to fit your specific experience.
* **📊 Hybrid Answer Evaluation:** Get feedback that's more than just a simple score. The app uses a sophisticated hybrid system:
    * **AI Rubric Score:** Gemini 1.5 Flash grades your answer on key metrics like the **STAR method**, clarity, and technical accuracy (`evaluation_prompts.py`).
    * **Semantic Score:** Your answer is compared to an AI-generated "ideal answer" using the `sentence-transformers` (`all-MiniLM-L6-v2`) model to gauge contextual and semantic similarity.
* **📈 Downloadable PDF Reports:** Receive a detailed, multi-page PDF report (`report_generator.py`) summarizing your performance, scores, key strengths, and areas for improvement for you to study offline.
* **💡 Cold-Start Mode:** Don't have a resume handy? You can still generate general, role-specific questions to start practicing immediately.

## 🚀 How It Works (Architecture)

This project uses a combination of NLP, retrieval, and generation techniques:

1.  **Question Generation:**
    * A resume (PDF) is read by `PyMuPDF`.
    * The raw text is fed into the `resume_parser.py`.
    * PII (emails, phones) is redacted using regex.
    * `spaCy` and a custom `EntityRuler` (built from `skill_taxonomy.json` based on the user's selected `job_category`) extract a structured JSON of `SKILLS`, `ORG`, etc.
    * The extracted `SKILLS` are passed to the `QuestionRetriever`.
    * The retriever filters the `question_bank.yml` for questions matching those skills.
    * The retrieved questions + resume JSON are sent to Gemini, which rewrites them into personalized questions.

2.  **Answer Evaluation:**
    * Gemini evaluates the user's answer against a detailed rubric (`EVALUATION_PROMPT_TEMPLATE`) to get a **Rubric Score**.
    * A separate AI call generates an "ideal reference answer" for the same question.
    * The `semantic_checker.py` module loads the `all-MiniLM-L6-v2` model from `sentence-transformers`.
    * It generates embeddings for the user's answer and the reference answer, computes the cosine similarity, and scales it to a 0-5 score. This is the **Semantic Score**.
    * These two scores are weighted to create a final, hybrid score.

## 🛠️ Tech Stack

* **Backend & AI:** Python, Google Gemini 1.5 Flash
* **Web Framework:** Gradio
* **NLP & Resume Parsing:** spaCy, PyMuPDF, pdf2image
* **Semantic Similarity:** sentence-transformers (`all-MiniLM-L6-v2`), PyTorch
* **Data Retrieval (RAG):** PyYAML
* **PDF Reporting:** ReportLab
* **Logging & Reliability:** `jsonlogger`, `tenacity`

## 🏁 Getting Started

Follow these steps to run the project locally.

### 1. Prerequisites

* Python 3.9+
* Git

### 2. Clone the Repository

```bash
git clone [https://github.com/your-username/interviewPreperationAIAssistant.git](https://github.com/your-username/interviewPreperationAIAssistant.git)
cd interviewPreperationAIAssistant
```

### 3. Set Up Dependencies

All required Python packages, including the specific `spaCy` model, are listed in `requirements.txt`.

[cite_start]Create a file named `requirements.txt` in the root of the project and paste the following content into it: [cite: 1]

```txt
# [cite_start]--- Core Application & PDF Handling --- [cite: 1]
[cite_start]gradio>=4.44.1 [cite: 1]
[cite_start]google-generativeai==0.7.1 [cite: 1]
[cite_start]PyMuPDF==1.24.2 [cite: 1]
[cite_start]pdf2image==1.17.0 [cite: 1]
[cite_start]reportlab==4.2.0 [cite: 1]
[cite_start]pillow==10.4.0 [cite: 1]

# [cite_start]--- NLP & Semantic Analysis --- [cite: 1]
[cite_start]spacy==3.7.5 [cite: 1]
[cite_start][https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl](https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl) [cite: 1]
[cite_start]sentence-transformers==3.0.1 [cite: 1]
[cite_start]torch==2.3.1 [cite: 1]

# [cite_start]--- RAG System & Data Handling --- [cite: 1]
[cite_start]faiss-cpu==1.8.0 [cite: 1]
[cite_start]PyYAML==6.0.1 [cite: 1]

# [cite_start]--- Reliability & Guardrails --- [cite: 1]
[cite_start]tenacity==8.4.1 [cite: 1]
[cite_start]python-json-logger==2.0.7 [cite: 1]
```

### 4. Install Dependencies

Now, run this command to install everything from the file:

```bash
pip install -r requirements.txt
```

### 5. Set Up Your API Key

This project requires a Google Gemini API key. You must set it as an environment variable.

**On macOS/Linux:**
```bash
export GEMINI_API_KEY='your_api_key_here'
```

**On Windows (Command Prompt):**
```bash
set GEMINI_API_KEY='your_api_key_here'
```

### 6. Run the Application

The main entry point is `app.py`.

```bash
python app.py
```

The application will now be running! Open the local URL (e.g., `http://127.0.0.1:7860`) in your browser.

## 📁 Project Structure

```
interviewPreperationAIAssistant/
├── app.py              <-- 🚀 Main entry point to run
├── requirements.txt    <-- Python dependencies
├── README.md           <-- You are here
├── audit_log.jsonl     <-- (Generated by logger)
└── src/
    ├── gradio_app.py   <-- Core Gradio UI and logic
    └── utils/
        ├── gemini_client.py        <-- Manages all Gemini API calls
        ├── pdf_reader.py           <-- Reads text from PDF files
        ├── resume_parser.py        <-- Parses resume text using spaCy
        ├── semantic_checker.py     <-- Calculates answer similarity
        ├── rag_retreiver.py        <-- Retrieves questions from YAML
        ├── report_generator.py     <-- Creates the final PDF report
        ├── prompts.py              <-- Prompts for question generation
        ├── evaluation_prompts.py   <-- Prompts for answer evaluation
        ├── audit_logger.py         <-- Configures JSON logging
        ├── question_bank.yml       <-- Curated RAG question database
        └── skill_taxonomy.json     <-- Skill list for resume parser
```

