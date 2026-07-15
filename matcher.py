import json
from pydantic import BaseModel, Field
from extractor import CandidateDetails, get_groq_client

class JobRequirements(BaseModel):
    min_experience_years: float = Field(default=0.0, description="Minimum years of experience required")
    required_skills: list[str] = Field(default=[], description="List of skills that are required or highly desired")
    project_preferences: str = Field(default="", description="Description of the types of projects required or preferred (e.g. 'Machine Learning projects', 'Cloud deployment')")

class SkillEvaluation(BaseModel):
    skill: str = Field(description="The required skill evaluated")
    matched: bool = Field(description="True if the candidate possesses this skill or an equivalent skill")
    details: str = Field(description="Justification of why the skill matched or why it is missing")

class MatchReport(BaseModel):
    overall_match_percentage: int = Field(description="An overall percentage from 0 to 100 representing how well the candidate matches the requirements.")
    experience_fit_score: int = Field(description="Score from 0 to 100 for experience fit")
    experience_fit_justification: str = Field(description="Justification for the experience score comparing candidate's experience to required experience.")
    skills_fit_score: int = Field(description="Score from 0 to 100 for skills fit")
    skills_evaluation: list[SkillEvaluation] = Field(description="Evaluation details for each required skill")
    projects_fit_score: int = Field(description="Score from 0 to 100 for project relevance")
    projects_fit_justification: str = Field(description="Justification for the projects score, describing how the candidate's projects fit the JD preferences.")
    key_strengths: list[str] = Field(description="List of candidate's key strengths for this role")
    identified_gaps: list[str] = Field(description="List of gaps or missing requirements")
    verdict: str = Field(description="Verdict: 'Call Candidate' or 'Do Not Contact'. Use 'Call Candidate' if overall_match_percentage >= 70, otherwise 'Do Not Contact'.")

def evaluate_match(candidate: CandidateDetails, requirements: JobRequirements, model: str = "llama-3.3-70b-versatile") -> MatchReport:
    client = get_groq_client()
    schema = MatchReport.model_json_schema()
    
    # Calculate programmatic heuristics to guide the LLM
    candidate_exp = candidate.experience_years
    required_exp = requirements.min_experience_years
    if required_exp == 0:
        exp_ratio = 1.0
    else:
        exp_ratio = min(candidate_exp / required_exp, 1.5)
        
    cand_skills_lower = [s.lower().strip() for s in candidate.skills]
    req_skills_matched = []
    for s in requirements.required_skills:
        s_lower = s.lower().strip()
        matched = any(s_lower in cs or cs in s_lower for cs in cand_skills_lower)
        req_skills_matched.append((s, matched))
    
    matched_count = sum(1 for _, m in req_skills_matched if m)
    total_skills = len(requirements.required_skills)
    skills_ratio = (matched_count / total_skills) if total_skills > 0 else 1.0
    
    heuristics = {
        "candidate_experience_years": candidate_exp,
        "required_experience_years": required_exp,
        "programmatic_experience_ratio": round(exp_ratio * 100),
        "programmatic_skills_matched_count": matched_count,
        "programmatic_skills_total_count": total_skills,
        "programmatic_skills_ratio": round(skills_ratio * 100)
    }
    
    system_prompt = f"""
You are a senior technical recruiter. Match the candidate's extracted details against the job requirements.
Evaluate:
1. Experience: Compare candidate experience years ({candidate.experience_years}) to the required minimum ({requirements.min_experience_years}).
2. Skills: Map the candidate's skills ({candidate.skills}) against the required list ({requirements.required_skills}). Support semantic matching (e.g. 'React.js' matches 'React', 'JS' matches 'JavaScript', 'Python3' matches 'Python').
3. Projects: Assess if the candidate's projects align with the project preferences: "{requirements.project_preferences}".

Output a detailed evaluation JSON strictly conforming to this schema.

JSON Schema:
{json.dumps(schema, indent=2)}
"""

    user_prompt = f"""
Candidate Details:
{candidate.model_dump_json(indent=2)}

Job Requirements:
{requirements.model_dump_json(indent=2)}

Programmatic Heuristics (for context):
{json.dumps(heuristics, indent=2)}

Perform the matching analysis and return the JSON.
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
    
    # Enforce threshold logic on the verdict
    score = data.get("overall_match_percentage", 0)
    if score >= 70:
        data["verdict"] = "Call Candidate"
    else:
        data["verdict"] = "Do Not Contact"
        
    return MatchReport(**data)
