import streamlit as st
import tempfile
import os
from pathlib import Path
from dotenv import load_dotenv

# Import our parser modules
from document_reader import read_document
from extractor import extract_candidate_details
from matcher import JobRequirements, evaluate_match
from main import extract_job_requirements

# Load environment variables
load_dotenv()
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

# Set Page Config
st.set_page_config(
    page_title="TalentMatch AI | Resume Parser & Matcher",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Glassmorphic Design
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Apply font to elements */
html, body, [class*="css"], .stMarkdown {
    font-family: 'Outfit', sans-serif;
}

/* Custom cards */
.glass-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 20px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
}

.metric-card {
    text-align: center;
    padding: 15px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.metric-value {
    font-size: 2.2rem;
    font-weight: 700;
    margin-bottom: 5px;
}

/* Status banners */
.call-banner {
    background: linear-gradient(135deg, rgba(39, 174, 96, 0.2) 0%, rgba(46, 204, 113, 0.1) 100%);
    border: 1px solid #2ecc71;
    color: #2ecc71;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    font-size: 1.5rem;
    font-weight: 700;
    margin: 20px 0;
    box-shadow: 0 0 15px rgba(46, 204, 113, 0.2);
}

.nocall-banner {
    background: linear-gradient(135deg, rgba(192, 57, 43, 0.2) 0%, rgba(231, 76, 60, 0.1) 100%);
    border: 1px solid #e74c3c;
    color: #e74c3c;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    font-size: 1.5rem;
    font-weight: 700;
    margin: 20px 0;
    box-shadow: 0 0 15px rgba(231, 76, 60, 0.2);
}

/* Score circle */
.score-circle {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(20,20,20,0.8) 60%, transparent 62%);
    border: 8px solid;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto;
    font-size: 2rem;
    font-weight: 700;
    box-shadow: 0 0 20px rgba(255, 255, 255, 0.05);
}

/* Bullet list style */
.bullet-item {
    font-size: 1.05rem;
    margin-bottom: 8px;
    display: flex;
    align-items: flex-start;
}
.bullet-icon {
    margin-right: 10px;
    margin-top: 3px;
}
</style>
""", unsafe_allow_html=True)

# App Header
st.title("💼 TalentMatch AI")
st.subheader("Smart Resume Parsing & Matching System for HR Professionals")
st.write("---")

# Sidebar settings
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/942/942748.png", width=80)
    st.header("Settings")
    
    # Model Selection
    model_choice = st.selectbox(
        "LLM Model",
        options=["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        index=0,
        help="Select the Groq model for analysis. 70B is recommended for complex reasoning."
    )
    
    match_threshold = st.slider(
        "HR Match Threshold (%)",
        min_value=50,
        max_value=95,
        value=70,
        step=5,
        help="The percentage score at which the system recommends calling the candidate."
    )
    
    st.info("💡 **How it works:**\n1. Input Job Requirements or paste a full Job Description.\n2. Upload a candidate's resume (PDF or DOCX).\n3. TalentMatch AI extracts structured profile information and computes a matching score with full justification.")

# Main layouts: Two columns for input
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("### 📝 1. Specify Job Requirements")
    
    input_mode = st.radio("Requirement Input Method", ["Paste Job Description Text", "Enter Criteria Manually"])
    
    if input_mode == "Paste Job Description Text":
        jd_text = st.text_area(
            "Paste the complete Job Description here...",
            height=300,
            placeholder="We are looking for a Software Engineer with 2+ years of experience in Python, C++, and Javascript. The candidate should have completed machine learning projects..."
        )
        requirements_obj = None
    else:
        req_exp = st.number_input("Minimum Required Experience (Years)", min_value=0.0, max_value=30.0, value=2.0, step=0.5)
        req_skills = st.text_input("Required Skills (Comma separated)", value="Python, C++, Java, JavaScript", placeholder="e.g. Python, SQL, React")
        req_proj = st.text_area("Preferred Projects / Focus Area", value="Machine Learning projects", placeholder="e.g. Fullstack web applications, Cloud migration, ML pipelines")
        
        skills_list = [s.strip() for s in req_skills.split(",") if s.strip()]
        requirements_obj = JobRequirements(
            min_experience_years=req_exp,
            required_skills=skills_list,
            project_preferences=req_proj
        )

with col_right:
    st.markdown("### 📄 2. Upload Candidate Resume")
    
    uploaded_file = st.file_uploader(
        "Upload Resume (PDF, DOCX, or TXT formats)",
        type=["pdf", "docx", "txt"],
        help="Make sure the file contains extractable text."
    )
    
    if uploaded_file is not None:
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": f"{uploaded_file.size / 1024:.2f} KB"}
        st.write(f"📁 **File:** `{uploaded_file.name}` ({file_details['FileSize']})")
        
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

# Trigger action
if uploaded_file is not None:
    st.write("")
    analyze_btn = st.button("🔍 Run Matching & Evaluation", type="primary", use_container_width=True)
    
    if analyze_btn:
        try:
            # Check API key before running
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                st.error("🔑 **API Key Missing!** Please ensure `GROQ_API_KEY` is set in the `.env` file in the project directory.")
                st.stop()
                
            with st.spinner("⏳ **Step 1: Reading Resume file contents...**"):
                resume_text = read_document(tmp_path)
                # Cleanup temp file
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            
            with st.spinner("🤖 **Step 2: Extracting candidate profile with AI...**"):
                candidate = extract_candidate_details(resume_text, model=model_choice)
                
            # If JD paste mode, extract requirements first
            if input_mode == "Paste Job Description Text":
                if not jd_text.strip():
                    st.warning("⚠️ Please paste a Job Description text first.")
                    st.stop()
                with st.spinner("📝 **Step 3: Extracting job requirements from JD...**"):
                    requirements_obj = extract_job_requirements(jd_text, model=model_choice)
            
            with st.spinner("📊 **Step 4: Scoring and evaluating match fit...**"):
                report = evaluate_match(candidate, requirements_obj, model=model_choice)
                
            # Draw Output Dashboard
            st.success("✅ **Analysis Complete!**")
            st.write("---")
            
            # Show overall verdict banner
            overall_score = report.overall_match_percentage
            
            # Determine verdict based on custom threshold
            if overall_score >= match_threshold:
                verdict_str = "Call Candidate"
                banner_class = "call-banner"
                banner_icon = "📞"
            else:
                verdict_str = "Do Not Contact"
                banner_class = "nocall-banner"
                banner_icon = "❌"
                
            st.markdown(f'<div class="{banner_class}">{banner_icon} Verdict: {verdict_str.upper()} (Score: {overall_score}%)</div>', unsafe_allow_html=True)
            
            # Main analysis columns
            col_metric_1, col_metric_2 = st.columns([1, 2], gap="large")
            
            with col_metric_1:
                # Radial/Circular Score Representation
                score_color = "#2ecc71" if overall_score >= match_threshold else ("#f1c40f" if overall_score >= 50 else "#e74c3c")
                st.markdown(f"""
                <div class="glass-card" style="text-align: center;">
                    <h4 style="margin-bottom: 20px; font-weight: 600;">Match Fit Score</h4>
                    <div class="score-circle" style="border-color: {score_color}; color: {score_color}; text-shadow: 0 0 10px {score_color}44;">
                        {overall_score}%
                    </div>
                    <div style="margin-top: 20px;">
                        <span style="font-size: 0.95rem; color: #888;">Required Threshold: {match_threshold}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Contact info
                st.markdown(f"""
                <div class="glass-card">
                    <h4 style="margin-top: 0; font-weight: 600;">Candidate Profile</h4>
                    <p>🧑 <b>Name:</b> {candidate.name}</p>
                    <p>📧 <b>Email:</b> {candidate.email if candidate.email else "Not found"}</p>
                    <p>📞 <b>Phone:</b> {candidate.phone if candidate.phone else "Not found"}</p>
                    <p>💼 <b>Experience:</b> {candidate.experience_years} years</p>
                </div>
                """, unsafe_allow_html=True)
                
            with col_metric_2:
                # Summary and breakdown
                st.markdown(f"""
                <div class="glass-card">
                    <h4 style="margin-top: 0; font-weight: 600;">Candidate Summary</h4>
                    <p style="font-size:1.1rem; line-height: 1.6; color: #ddd;">{candidate.summary}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Fit breakdowns
                st.markdown(f"""
                <div class="glass-card">
                    <h4 style="margin-top: 0; font-weight: 600; margin-bottom: 15px;">Requirement Scoring Breakdown</h4>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span>💼 Experience Fit Score</span>
                        <b>{report.experience_fit_score}/100</b>
                    </div>
                    <p style="font-size: 0.95rem; color: #aaa; margin-bottom: 20px;">{report.experience_fit_justification}</p>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span>🛠️ Skills Fit Score</span>
                        <b>{report.skills_fit_score}/100</b>
                    </div>
                    <p style="font-size: 0.95rem; color: #aaa; margin-bottom: 20px;">Candidate skills: {", ".join(candidate.skills)}</p>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span>🚀 Projects Fit Score</span>
                        <b>{report.projects_fit_score}/100</b>
                    </div>
                    <p style="font-size: 0.95rem; color: #aaa; margin-bottom: 10px;">{report.projects_fit_justification}</p>
                </div>
                """, unsafe_allow_html=True)
                
            # Skills matching table
            st.markdown("### 🛠️ Detailed Skill-by-Skill Evaluation")
            
            # Formulate a grid/table
            skills_data = []
            for item in report.skills_evaluation:
                status_icon = "🟢 Yes" if item.matched else "🔴 No"
                skills_data.append({
                    "Required Skill": item.skill,
                    "Matched": status_icon,
                    "Analysis Details": item.details
                })
            st.table(skills_data)
            
            # Strengths & Gaps
            col_strengths, col_gaps = st.columns(2)
            
            with col_strengths:
                st.markdown(f"""
                <div class="glass-card" style="border-left: 5px solid #2ecc71;">
                    <h4 style="margin-top:0; color: #2ecc71; font-weight: 600;">🌟 Key Strengths</h4>
                    {"".join([f'<div class="bullet-item"><span class="bullet-icon">🟢</span>{s}</div>' for s in report.key_strengths])}
                </div>
                """, unsafe_allow_html=True)
                
            with col_gaps:
                st.markdown(f"""
                <div class="glass-card" style="border-left: 5px solid #e74c3c;">
                    <h4 style="margin-top:0; color: #e74c3c; font-weight: 600;">⚠️ Identified Gaps</h4>
                    {"".join([f'<div class="bullet-item"><span class="bullet-icon">🔴</span>{g}</div>' for g in report.identified_gaps]) if report.identified_gaps else '<div class="bullet-item"><span class="bullet-icon">🟢</span>No major gaps identified!</div>'}
                </div>
                """, unsafe_allow_html=True)
                
            # Candidate Projects Detail
            if candidate.projects:
                st.markdown("### 🚀 Extracted Candidate Projects")
                for p in candidate.projects:
                    with st.expander(f"📁 Project: {p.title}", expanded=True):
                        st.markdown(f"**Description:** {p.description}")
                        if p.technologies:
                            st.markdown(f"**Technologies used:** " + ", ".join([f"`{t}`" for t in p.technologies]))
                            
        except Exception as e:
            st.error(f"❌ **An error occurred during analysis:** {e}")
            st.exception(e)
else:
    st.info("👈 **Upload a candidate resume to begin the evaluation process.**")
