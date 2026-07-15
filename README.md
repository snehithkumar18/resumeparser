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

## 🚀 4. How to Use the Project

Follow these steps to configure, run, and test the project locally.

### Step 1: Environment & API Key Setup

1. Make sure you have a `.env` file in the parent directory (`c:/Users/NEHITH/Ai_engineer/.env`) or directly inside this `resume_parser` directory.
2. The `.env` file must contain your Groq API Key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

### Step 2: Install Dependencies
If you are running the project in a new environment, make sure to install the dependencies inside the virtual environment:
```bash
# Using uv (fastest)
uv pip install -r pyproject.toml

# Or using standard pip
pip install groq pydantic python-dotenv pypdf python-docx streamlit rich reportlab
```

### Step 3: Generate Mock Resumes & JDs for Testing
We provide a helper utility to instantly generate sample PDF and Word resumes, as well as Job Descriptions, so you can test the system right away:
```bash
# From the resume_parser directory:
..\.venv\Scripts\python generate_samples.py
```
This generates the following files in the `samples/` subdirectory:
*   `samples/resume_john_doe.docx`: Fullstack Web Developer profile.
*   `samples/resume_sarah_smith.pdf`: Data Scientist / ML Engineer profile.
*   `samples/job_desc_web.txt`: Web Developer job description.
*   `samples/job_desc_ml.txt`: Machine Learning Engineer job description.

---

### Step 4: Using the CLI Interface
The CLI tool (`main.py`) supports two ways of providing job requirements:

#### Option A: Match using a Job Description file (`--jd`)
Pass the path to the resume and the job description text file:
```powershell
# Set UTF-8 encoding for Windows terminals to display modern UI graphics:
$env:PYTHONUTF8="1"

# Run match
..\.venv\Scripts\python main.py --resume samples/resume_john_doe.docx --jd samples/job_desc_web.txt
```

#### Option B: Match using Manual Criteria
If you don't have a job description file, you can pass criteria using CLI flags:
*   `--resume`: Path to the resume file (Required)
*   `--skills`: Comma-separated list of required skills (Required)
*   `--exp`: Minimum required years of experience (Default: 0.0)
*   `--projects`: Description of the project preferences (Default: "")

Example:
```powershell
$env:PYTHONUTF8="1"
..\.venv\Scripts\python main.py --resume samples/resume_sarah_smith.pdf --skills "Python, PyTorch, SQL" --exp 4.0 --projects "deep learning chatbot"
```

---

### Step 5: Using the Streamlit Web Dashboard
The Streamlit dashboard (`app.py`) provides an interactive, visual interface for HR professionals.

#### 1. Launch the Server
Start the Streamlit application from your terminal:
```bash
..\.venv\Scripts\streamlit run app.py --server.port 8501 --server.address localhost
```
Open **[http://localhost:8501](http://localhost:8501)** in your web browser.

#### 2. Using the Dashboard
*   **Sidebar Settings**: 
    *   **LLM Model**: Switch between `llama-3.3-70b-versatile` (high accuracy) and `llama-3.1-8b-instant` (high speed).
    *   **HR Match Threshold**: Set the score percentage (e.g. 70%) required to trigger the green "Call Candidate" recommendation.
*   **Input Job Requirements**: 
    *   Choose *Paste Job Description Text* to copy-paste an entire JD (the app will extract requirements automatically).
    *   Choose *Enter Criteria Manually* to enter exact years, skills, and project guidelines.
*   **Upload and Analyze**:
    *   Drag and drop a candidate's resume (PDF, Word, or TXT).
    *   Click **Run Matching & Evaluation** to run the matching engine and view the results.
