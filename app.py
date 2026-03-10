from flask import Flask, render_template, request
import os
import uuid
from werkzeug.utils import secure_filename
from utils import extract_text_from_pdf, analyze_resume, improve_resume

app = Flask(__name__, template_folder=".")

# Folder to save uploaded PDFs (must be inside 'static' for browser access)
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Upload & Analyze Resume
# -----------------------------
@app.route("/upload", methods=["POST"])
def upload_resume():
    if "resume" not in request.files:
        return "No file uploaded."

    file = request.files["resume"]
    job_role = request.form.get("job_role")

    if file.filename == "":
        return "No file selected."

    if not job_role:
        return "Please enter a target job role."

    if not file.filename.endswith(".pdf"):
        return "Please upload a PDF file only."

    # Secure file name and create unique name
    filename = secure_filename(file.filename)
    unique_name = str(uuid.uuid4()) + "_" + filename
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(filepath)

    # URL for browser access
    uploaded_pdf_url = f"/{filepath}"

    try:
        # Extract text from PDF
        text = extract_text_from_pdf(filepath)
        if not text.strip():
            return "Could not extract text from this PDF."

        # Analyze resume
        result = analyze_resume(text, job_role)  # returns dict with score, factor_scores, skill_tags, suggestions, etc.

        # Ensure job_role is included in result
        if "job_role" not in result:
            result["job_role"] = job_role

        return render_template(
            "result.html",
            original_text=text,
            improved_resume=None,
            uploaded_pdf=uploaded_pdf_url,
            **result
        )

    except Exception as e:
        return f"Error processing resume: {str(e)}"


# -----------------------------
# Improve Resume
# -----------------------------
@app.route("/improve", methods=["POST"])
def improve_resume_route():
    resume_text = request.form.get("resume_text")
    job_role = request.form.get("job_role")
    uploaded_pdf = request.form.get("uploaded_pdf")  # Keep the PDF URL

    if not resume_text:
        return "No resume text found."

    if not job_role:
        return "Job role missing."

    try:
        # Call AI improvement function
        improved_resume_text = improve_resume(resume_text, job_role)

        # Render the same result page with improved resume AND keep PDF visible
        return render_template(
            "result.html",
            original_text=resume_text,
            improved_resume=improved_resume_text,
            uploaded_pdf=uploaded_pdf,  # Keep PDF
            score=None,
            factor_scores=None,
            suggestions=None,
            skill_tags=None,
            word_count=len(resume_text.split()),
            job_role=job_role
        )

    except Exception as e:
        return f"Error improving resume: {str(e)}"
    
if __name__ == "__main__":
    app.run(debug=True)