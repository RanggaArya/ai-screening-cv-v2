import json
import numpy as np
import google.generativeai as genai
from pypdf import PdfReader
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import settings

# Konfigurasi Gemini API
genai.configure(api_key=settings.GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# Path vector.json
VECTOR_PATH = "app/data/vector.json"

# Load vectors dari file
with open(VECTOR_PATH, "r", encoding="utf-8") as f:
    VECTORS = json.load(f)

for v in VECTORS:
    v["embedding"] = np.array(v["embedding"], dtype=float)


# ===========================
# Fungsi Utility
# ===========================
def parse_pdf(file_path: str) -> str:
    """Membaca PDF dan mengembalikan teks."""
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        print(f"Error parsing PDF {file_path}: {e}")
    return text.strip()


def _find_similar_context(query: str, top_k: int = 5) -> str:
    """
    Cari konteks paling relevan dari vector.json menggunakan cosine similarity.
    """
    query_vec = np.random.normal(0, 1, len(VECTORS[0]["embedding"]))
    query_vec = query_vec / np.linalg.norm(query_vec)

    sims = []
    for v in VECTORS:
        sim = np.dot(query_vec, v["embedding"]) / (
            np.linalg.norm(query_vec) * np.linalg.norm(v["embedding"])
        )
        sims.append((v["text"], float(sim)))

    sims.sort(key=lambda x: x[1], reverse=True)
    top_contexts = [t for t, _ in sims[:top_k]]
    return "\n---\n".join(top_contexts)


# ===========================
# Fungsi LLM (Gemini)
# ===========================
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def llm_call(prompt: str) -> dict:
    """Memanggil Gemini dan memastikan output JSON valid."""
    try:
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.3
        )
        response = gemini_model.generate_content(prompt, generation_config=generation_config)
        cleaned = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned)
    except Exception as e:
        print(f"Gemini error: {e}")
        raise


# ===========================
# Fungsi Pipeline
# ===========================
def run_cv_evaluation(cv_text: str, job_title: str) -> dict:
    """Evaluasi CV berbasis vector.json."""
    print("Running CV Evaluation...")
    context = _find_similar_context(f"CV evaluation {job_title}")
    prompt = f"""
    You are an expert recruiter. Evaluate this CV for a '{job_title}' position.

    === Context Knowledge ===
    {context}

    === Candidate CV ===
    {cv_text}

    Return JSON:
    {{
        "cv_match_rate": float (0.0–1.0),
        "cv_feedback": string
    }}
    """
    return llm_call(prompt)


def run_project_evaluation(report_text: str) -> dict:
    """Evaluasi laporan proyek."""
    print("Running Project Evaluation...")
    context = _find_similar_context("project evaluation criteria")
    prompt = f"""
    You are a senior engineer evaluating a project report.

    === Context ===
    {context}

    === Report ===
    {report_text}

    Return JSON:
    {{
        "project_score": float (1–5),
        "project_feedback": string
    }}
    """
    return llm_call(prompt)


def run_final_summary(cv_feedback: str, project_feedback: str) -> dict:
    """Membuat ringkasan akhir."""
    print("Running Final Summary...")
    prompt = f"""
    You are a hiring manager. Based on the evaluations below, create a short summary.

    CV Feedback: {cv_feedback}
    Project Feedback: {project_feedback}

    Return JSON:
    {{
        "overall_summary": string
    }}
    """
    return llm_call(prompt)
