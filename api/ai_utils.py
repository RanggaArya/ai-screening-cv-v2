import json
import chromadb
import google.generativeai as genai # type: ignore
from pypdf import PdfReader
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import settings

# Konfigurasi Klien Gemini
# Konfigurasi API Key untuk Google Gemini
genai.configure(api_key=settings.GOOGLE_API_KEY)
#genai.configure(api_key="AIzaSyCLwcIQJ-PWVfwiJuy3zRdUq7uzHkhu78k") 

# Inisialisasi model. 'gemini-2.5-flash' adalah model yang cepat dan efisien.
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# Klien ChromaDB untuk mengambil konteks
client_chroma = chromadb.PersistentClient(path="chroma_db_storage")
collection = client_chroma.get_collection(name="job_screening_docs")

#Fungsi Helper

def parse_pdf(file_path: str) -> str:
    """Membaca file PDF dan mengembalikan konten teksnya."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error parsing PDF {file_path}: {e}")
        return ""

def retrieve_context(query: str, source_file_filter: list[str], n_results: int = 5) -> str:
    """Mengambil konteks yang relevan dari ChromaDB berdasarkan query dan filter."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"source_file": {"$in": source_file_filter}}
    )
    context = "\n---\n".join(results['documents'][0])
    return context

# Fungsi LLM Call

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def llm_call(prompt: str) -> dict:
    """
    Melakukan panggilan ke Gemini dengan penanganan retry dan memastikan output JSON.
    """
    try:
        print("Mencoba memanggil API Gemini...")
        # Gemini dikonfigurasi untuk menghasilkan JSON dan suhu rendah
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
        # Melakukan panggilan ke Gemini
        response = gemini_model.generate_content(prompt, generation_config=generation_config)
        
        print("Berhasil menerima respons dari Gemini.")
        # Membersihkan dan mem-parsing output JSON
        cleaned_json = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_json)
    except Exception as e:
        print(f"!!! TERJADI ERROR SAAT MEMANGGIL GEMINI: {e}")
        raise

# Fungsi Utama Pipeline AI

def run_cv_evaluation(cv_text: str, job_title: str) -> dict:
    """Mengevaluasi CV menggunakan RAG dan Gemini."""
    print("Running CV Evaluation...")
    context_query = f"Skills and experience for a {job_title}"
    context = retrieve_context(
        query=context_query,
        source_file_filter=["backend_job_description.pdf", "cv_scoring_rubric.pdf"]
    )
    prompt = f"""
    You are an expert technical recruiter. Evaluate the following candidate's CV for a '{job_title}' position.
    Use the provided Job Description and Scoring Rubric as your ground truth.

    **Ground Truth Context:**
    {context}

    **Candidate's CV:**
    {cv_text}

    **Task:**
    Based on the context and CV, provide a score and feedback. The final 'cv_match_rate' must be a weighted average based on the rubric, converted to a 0-1 decimal. Calculate it precisely.
    Return a valid JSON object with ONLY the following keys and appropriate data types:
    - "cv_match_rate": float (a value between 0.0 and 1.0)
    - "cv_feedback": string (a concise summary of strengths and weaknesses)
    """
    return llm_call(prompt)

def run_project_evaluation(report_text: str) -> dict:
    """Mengevaluasi laporan proyek menggunakan RAG dan Gemini."""
    print("Running Project Evaluation...")
    context_query = "Evaluation criteria for the case study project"
    context = retrieve_context(
        query=context_query,
        source_file_filter=["case_study_brief.pdf", "project_scoring_rubric.pdf"]
    )
    prompt = f"""
    You are a senior backend engineer. Evaluate the candidate's project report for our take-home case study.
    Use the provided Case Study Brief and Project Scoring Rubric as your ground truth.

    **Ground Truth Context:**
    {context}

    **Candidate's Project Report:**
    {report_text}

    **Task:**
    Based on the context and the report, provide a score and feedback. The final 'project_score' must be a weighted average of the parameters on a 1-5 scale. Calculate it precisely.
    Return a valid JSON object with ONLY the following keys and appropriate data types:
    - "project_score": float (a value between 1.0 and 5.0)
    - "project_feedback": string (a concise summary of what was done well and what could be improved)
    """
    return llm_call(prompt)

def run_final_summary(cv_feedback: str, project_feedback: str) -> dict:
    """Membuat ringkasan akhir berdasarkan hasil evaluasi."""
    print("Running Final Summary...")
    prompt = f"""
    You are a hiring manager. Based on the following evaluation feedback, create a concise overall summary (3-5 sentences) about the candidate.
    Highlight their strengths, mention any gaps, and give a final recommendation.

    **Task:**
    Return a valid JSON object with ONLY one key:
    - "overall_summary": string
    """
    return llm_call(prompt)
