import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field

# Load environment variables from current directory or parent directory
load_dotenv()
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

class Project(BaseModel):
    title: str = Field(description="Title of the project")
    description: str = Field(description="Brief description of what the project does and the candidate's contribution")
    technologies: list[str] = Field(default=[], description="List of technologies, frameworks, or programming languages used in the project")

class CandidateDetails(BaseModel):
    name: str = Field(description="Full name of the candidate")
    email: str = Field(description="Email address of the candidate, empty string if not found")
    phone: str = Field(description="Phone number of the candidate, empty string if not found")
    skills: list[str] = Field(default=[], description="List of technical skills, programming languages, tools, frameworks, and databases mentioned")
    experience_years: float = Field(default=0.0, description="Total years of work experience mentioned or calculated from job durations")
    projects: list[Project] = Field(default=[], description="List of projects completed by the candidate")
    summary: str = Field(description="A brief professional summary of the candidate based on the resume")

def get_groq_client() -> Groq:
    """Initializes and returns the Groq client using environment variable."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment. Please check your .env file.")
    return Groq(api_key=api_key)

def extract_candidate_details(resume_text: str, model: str = "llama-3.3-70b-versatile") -> CandidateDetails:
    """Uses Groq LLM to extract structured details from the raw resume text."""
    client = get_groq_client()
    
    schema = CandidateDetails.model_json_schema()
    
    system_prompt = f"""
You are a world-class HR assistant. Extract the candidate's professional details strictly based on this JSON schema and output a valid JSON object.
Do not include any chat prefix, suffix, or extra formatting. Output only the raw JSON.

JSON Schema:
{json.dumps(schema, indent=2)}
"""
    
    user_prompt = f"""
Extract candidate details from the following resume text:

--- RESUME TEXT START ---
{resume_text}
--- RESUME TEXT END ---
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"}
    )
    
    answer = response.choices[0].message.content
    data = json.loads(answer)
    return CandidateDetails(**data)
