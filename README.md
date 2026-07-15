# TalentMatch AI: Resume Parser & Matcher

TalentMatch AI is an automated resume parsing and job-matching system built for HR professionals. It extracts key details (skills, experience, and projects) from candidate resumes (PDF, Word, or TXT formats) and matches them against job requirements using the Groq API and structured Pydantic data schemas.

---

## 🛠️ 1. Tech Stack & Libraries

*   **LLM Engine**: **Groq SDK** (`llama-3.3-70b-versatile` model) for fast reasoning and structured outputs.
*   **Validation & Serialization**: **Pydantic v2** (`pydantic`) to declare schemas and validate JSON responses.
*   **Document Readers**:
    *   `pypdf`: Extracts text from PDF resumes.
    *   `python-docx`: Extracts text from Word documents (including tables).
*   **User Interfaces**:
    *   **Streamlit**: For a visual, glassmorphic, interactive HR dashboard.
    *   **Rich**: For a colorful, styled command-line interface.
*   **Testing Utilities**:
    *   `reportlab`: Used to programmatically generate styled, multi-page PDF resumes for testing.

---

## 📂 2. Project Architecture & Modules

The application is structured into modular components:

```
resume_parser/
├── pyproject.toml         # Dependency configurations
├── document_reader.py     # PDF & Word text extractor
├── extractor.py           # LLM Structured parsing & Pydantic schemas
├── matcher.py             # Matcher & scoring engine
├── main.py                # Console CLI interface
├── app.py                 # Streamlit web dashboard
├── generate_samples.py    # Test file generator
└── samples/               # Sample JDs & Resumes folder (auto-generated)
```

### 1. `document_reader.py`
Reads files and extracts text.
*   **PDF**: Scans page-by-page using `pypdf.PdfReader`.
*   **Word**: Reads paragraphs and tables using `python-docx`. Table cells are separated by a `|` character to preserve visual grid formatting for the LLM.
*   **Plaintext**: Directly opens `.txt` or `.md` files.

### 2. `extractor.py`
Specifies data types using Pydantic models:
*   `Project`: Maps project title, description, and technologies.
*   `CandidateDetails`: Maps name, email, phone, experience years, skills, projects, and professional summary.
*   **Flow**: Sends the JSON schema of `CandidateDetails` to Groq and calls the LLM with `response_format={"type": "json_object"}`. The JSON response is validated by Pydantic before returning.

### 3. `matcher.py`
Performs the matching logic against candidate details.
*   `JobRequirements`: Maps minimum experience years, required skills, and project preferences.
*   `MatchReport`: Compiles the overall score, strengths, gaps, skill evaluation checklist, and verdict.
*   **Flow**: Programmatically calculates keyword matches and experience ratios. It feeds these calculations as *heuristics* alongside the resume and requirements to the LLM. The LLM handles synonyms (e.g. "ReactJS" matching "React") and project relevance. If the score is $\ge 70\%$, a `"Call Candidate"` recommendation is made, otherwise `"Do Not Contact"`.

---

## 🔒 3. Background Validation & Matching Logic

The matching and validation pipeline ensures high accuracy and prevents AI hallucination:

1.  **JSON Constraints**: By converting Pydantic models to JSON schema (`model_json_schema()`) and supplying them to the LLM, we guarantee that the output structure matches the expected key names and types.
2.  **Grounded Heuristics**: The matcher calculates programmatic baseline statistics (e.g., exact keyword matches and experience numbers) and passes them to the LLM. This grounds the LLM’s final scoring, ensuring it stays mathematically aligned with requirements while maintaining semantic flexibility (like understanding that a "Deep Learning Chatbot" meets a "Machine Learning project" preference).

---

## 🚀 4. How to Set Up and Test the Project

### Prerequisites
Make sure your terminal is opened in `c:\Users\NEHITH\Ai_engineer\resume_parser`.

### 1. Re-generate Samples
Run the sample generator script to create test resumes (DOCX and PDF) and Job Description templates inside the `samples/` folder:
```bash
..\.venv\Scripts\python generate_samples.py
```

### 2. Run the CLI
Use the command-line interface to match resumes against JDs directly in your terminal. We pass `$env:PYTHONUTF8="1"` to support spinner/checkmark symbols on Windows:

*   **Positive Match (John Doe vs Web JD):**
    ```powershell
    $env:PYTHONUTF8="1"; ..\.venv\Scripts\python main.py --resume samples/resume_john_doe.docx --jd samples/job_desc_web.txt
    ```
*   **Positive Match (Sarah Smith vs ML JD):**
    ```powershell
    $env:PYTHONUTF8="1"; ..\.venv\Scripts\python main.py --resume samples/resume_sarah_smith.pdf --jd samples/job_desc_ml.txt
    ```
*   **Negative Match (John Doe vs ML JD):**
    ```powershell
    $env:PYTHONUTF8="1"; ..\.venv\Scripts\python main.py --resume samples/resume_john_doe.docx --jd samples/job_desc_ml.txt
    ```

### 3. Run the Streamlit Dashboard
Launch the web interface locally to upload resumes, enter criteria manually, or paste job descriptions:
```bash
..\.venv\Scripts\streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your web browser. Drag and drop any resume from the `samples/` folder to view the interactive dashboard.
