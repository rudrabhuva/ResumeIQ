import pdfplumber
import re
from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get the API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# -----------------------------
# Extract Text From PDF
# -----------------------------
def extract_text_from_pdf(filepath):
    text = ""

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"

    return text


# -----------------------------
# Generate AI Suggestions (Job Specific)
# -----------------------------
def generate_suggestions(resume_text, job_role):

    prompt = f"""
You are a senior HR manager and ATS optimization expert.

The candidate is applying for the following role:
{job_role}

Analyze the resume specifically for this role.

Evaluation Criteria:
- Skill relevance for {job_role}
- ATS compatibility
- Achievement impact
- Missing keywords for {job_role}
- Formatting quality
- Quantification of results

Respond STRICTLY in this format:

OVERALL_SCORE: (0-100)

SKILLS_SCORE: (0-100)
KEYWORDS_SCORE: (0-100)
ACHIEVEMENTS_SCORE: (0-100)
ATS_OPTIMIZATION_SCORE: (0-100)
FORMATTING_SCORE: (0-100)

STRENGTHS:
- 
- 
- 

WEAKNESSES:
- 
- 
- 

MISSING_SECTIONS:
- 

TECHNICAL_SKILL_GAPS:
- 

ATS_IMPROVEMENTS:
- 

ACTIONABLE_IMPROVEMENTS:
1.
2.
3.

Resume:
{resume_text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert ATS resume reviewer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=1500
    )

    return response.choices[0].message.content


# -----------------------------
# Analyze Resume
# -----------------------------
def analyze_resume(text, job_role):

    word_count = len(text.split())

    if len(text) > 8000:
        text = text[:8000]

    ai_response = generate_suggestions(text, job_role)

    # Extract overall score
    score = 0
    match = re.search(r"OVERALL_SCORE:\s*(\d+)", ai_response)
    if match:
        score = int(match.group(1))

    # Extract factor scores for radar chart
    factors = ["Skills", "Keywords", "Achievements", "ATS Optimization", "Formatting"]
    factor_scores = {}
    for factor in factors:
        regex = re.compile(rf"{factor.upper().replace(' ', '_')}_SCORE:\s*(\d+)")
        m = regex.search(ai_response)
        factor_scores[factor] = int(m.group(1)) if m else 0

    return {
        "word_count": word_count,
        "score": score,
        "suggestions": ai_response,
        "job_role": job_role,
        "factor_scores": factor_scores
    }


# -----------------------------
# Improve Entire Resume (Job Specific)
# -----------------------------
def improve_resume(resume_text, job_role):

    prompt = f"""
You are a professional resume writer.

Rewrite and optimize this resume specifically for the role:
{job_role}

Rules:
- Tailor skills for {job_role}
- Add relevant keywords
- Improve grammar
- Use strong action verbs
- Make achievements measurable
- Optimize for ATS
- Keep structure clean

Return ONLY the improved resume.

Resume:
{resume_text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert resume writer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=2000
    )

    return response.choices[0].message.content


# -----------------------------
# Step 3: Word Count & Keyword Density Analysis
# -----------------------------
def keyword_density_analysis(resume_text, keywords):
    """
    Analyzes the resume for total word count and keyword density.

    Args:
        resume_text (str): The full resume text.
        keywords (list): List of keywords/skills to check in the resume.

    Returns:
        dict: {
            "word_count": int,
            "keyword_counts": dict,      # {keyword: count in resume}
            "keyword_density": dict      # {keyword: % of total words}
        }
    """
    words = resume_text.split()
    total_words = len(words)

    keyword_counts = {}
    keyword_density = {}

    for kw in keywords:
        count = resume_text.lower().count(kw.lower())
        keyword_counts[kw] = count
        keyword_density[kw] = round((count / total_words) * 100, 2) if total_words > 0 else 0

    return {
        "word_count": total_words,
        "keyword_counts": keyword_counts,
        "keyword_density": keyword_density
    }
# -----------------------------
# Skill Tagging / Auto-Categorization
# -----------------------------
def tag_skills(resume_text, skill_list):
    """
    Detects and tags skills/technologies present in a resume.

    Args:
        resume_text (str): Full text of the resume.
        skill_list (list): List of skills/technologies to check.

    Returns:
        list: Skills found in the resume as tags.
    """
    resume_lower = resume_text.lower()
    tags = []

    for skill in skill_list:
        # Check if the skill exists in resume text (case-insensitive)
        if skill.lower() in resume_lower:
            tags.append(skill)

    return tags