import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

from document_reader import read_document
from extractor import extract_candidate_details
from matcher import JobRequirements, evaluate_match

# Rich UI imports
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

# Load environment variables
load_dotenv()
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

def extract_job_requirements(jd_text: str, model: str = "llama-3.3-70b-versatile") -> JobRequirements:
    """Helper to extract structured job requirements from raw job description text using Groq."""
    from extractor import get_groq_client
    import json
    
    client = get_groq_client()
    schema = JobRequirements.model_json_schema()
    
    system_prompt = f"""
You are an expert recruiter. Extract the structured job requirements from the job description text strictly based on this JSON schema.
Convert experience requirements to numerical years (e.g. '2+ years' or '2 years' -> 2.0, '6 months' -> 0.5, 'freshers' or no experience -> 0.0) and extract clean, lowercase keywords for required skills.

JSON Schema:
{json.dumps(schema, indent=2)}
"""
    
    user_prompt = f"""
Job Description Text:
{jd_text}

Extract requirements:
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
    return JobRequirements(**data)

def main():
    console = Console()
    
    parser = argparse.ArgumentParser(description="Resume Parser and Matcher CLI")
    parser.add_argument("--resume", type=str, required=True, help="Path to the candidate's resume (PDF or DOCX)")
    parser.add_argument("--jd", type=str, help="Path to the job description text file")
    parser.add_argument("--skills", type=str, help="Comma-separated list of required skills (used if --jd is not provided)")
    parser.add_argument("--exp", type=float, default=0.0, help="Minimum required years of experience (used if --jd is not provided)")
    parser.add_argument("--projects", type=str, default="", help="Description of project preferences (used if --jd is not provided)")
    
    args = parser.parse_args()
    
    resume_path = Path(args.resume)
    if not resume_path.exists():
        console.print(f"[bold red]Error:[/] Resume file not found at {resume_path}", style="red")
        sys.exit(1)
        
    requirements = None
    if args.jd:
        jd_path = Path(args.jd)
        if not jd_path.exists():
            console.print(f"[bold red]Error:[/] Job Description file not found at {jd_path}", style="red")
            sys.exit(1)
        with open(jd_path, "r", encoding="utf-8") as f:
            jd_text = f.read()
            
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            progress.add_task(description="Extracting job requirements from Job Description using Groq...", total=None)
            try:
                requirements = extract_job_requirements(jd_text)
            except Exception as e:
                console.print(f"[bold red]Error extracting JD requirements:[/] {e}", style="red")
                sys.exit(1)
    else:
        # Build from CLI arguments
        if not args.skills:
            console.print("[bold red]Error:[/] Please provide either a Job Description file (--jd) or a list of skills (--skills)", style="red")
            sys.exit(1)
        skills_list = [s.strip() for s in args.skills.split(",")]
        requirements = JobRequirements(
            min_experience_years=args.exp,
            required_skills=skills_list,
            project_preferences=args.projects
        )
        
    console.print(Panel.fit("[bold cyan]Resume Parser & Matcher CLI[/]\nReady to parse and match candidate resume...", border_style="cyan"))
    
    # 1. Read document
    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            progress.add_task(description=f"Reading resume: {resume_path.name}...", total=None)
            resume_text = read_document(resume_path)
    except Exception as e:
        console.print(f"[bold red]Error reading document:[/] {e}", style="red")
        sys.exit(1)
        
    # 2. Extract Candidate Details
    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            progress.add_task(description="Extracting profile details using Groq...", total=None)
            candidate = extract_candidate_details(resume_text)
    except Exception as e:
        console.print(f"[bold red]Error extracting candidate details:[/] {e}", style="red")
        sys.exit(1)
        
    # 3. Match against Job Description
    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            progress.add_task(description="Matching resume profile against requirements...", total=None)
            report = evaluate_match(candidate, requirements)
    except Exception as e:
        console.print(f"[bold red]Error evaluating match:[/] {e}", style="red")
        sys.exit(1)
        
    # Output results
    console.print("\n")
    
    # Candidate Summary Panel
    candidate_info = f"[bold]Name:[/] {candidate.name}\n"
    if candidate.email:
        candidate_info += f"[bold]Email:[/] {candidate.email}\n"
    if candidate.phone:
        candidate_info += f"[bold]Phone:[/] {candidate.phone}\n"
    candidate_info += f"[bold]Experience:[/] {candidate.experience_years} years\n"
    candidate_info += f"[bold]Summary:[/] {candidate.summary}"
    
    console.print(Panel(candidate_info, title="[bold green]Candidate Profile[/]", border_style="green"))
    
    # Skills Table
    skills_table = Table(title="[bold blue]Skills Evaluation[/]", show_header=True, header_style="bold blue")
    skills_table.add_column("Required Skill", style="cyan")
    skills_table.add_column("Matched", justify="center")
    skills_table.add_column("Details", style="yellow")
    
    for eval_item in report.skills_evaluation:
        matched_str = "[bold green]✔[/]" if eval_item.matched else "[bold red]✘[/]"
        skills_table.add_row(eval_item.skill, matched_str, eval_item.details)
        
    console.print(skills_table)
    
    # Experience and Projects Score
    exp_and_proj = Table(show_header=False, box=None)
    exp_and_proj.add_row(
        "[bold]Experience Fit Score:[/] " + f"{report.experience_fit_score}/100", 
        f"[dim]{report.experience_fit_justification}[/]"
    )
    exp_and_proj.add_row(
        "[bold]Projects Fit Score:[/]     " + f"{report.projects_fit_score}/100", 
        f"[dim]{report.projects_fit_justification}[/]"
    )
    console.print(Panel(exp_and_proj, title="[bold magenta]Experience & Projects Fit[/]", border_style="magenta"))
    
    # Verdict Panel
    verdict_color = "green" if report.overall_match_percentage >= 70 else "red"
    verdict_text = f"[bold]Overall Match Score:[/] {report.overall_match_percentage}%\n"
    verdict_text += f"[bold]HR Recommendation:[/] {report.verdict.upper()}\n\n"
    verdict_text += f"[bold]Key Strengths:\n[/]" + "\n".join([f" • {s}" for s in report.key_strengths]) + "\n\n"
    verdict_text += f"[bold]Identified Gaps:\n[/]" + "\n".join([f" • {g}" for g in report.identified_gaps])
    
    console.print(Panel(verdict_text, title=f"[bold {verdict_color}]Verdict: {report.verdict.upper()}[/]", border_style=verdict_color))

if __name__ == "__main__":
    main()
