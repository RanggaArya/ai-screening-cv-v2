import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from typing import List
from . import schemas, tasks
from .job_store import create_job, get_job_status

# Buat folder uploads jika belum ada
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Simpan path file yang diunggah berdasarkan ID-nya
# Dalam aplikasi nyata, ini akan ada di database.
document_paths: dict[str, str] = {}

app = FastAPI(title="AI CV Evaluator API")

@app.post("/upload", response_model=schemas.UploadResponse)
async def upload_files(
    cv_file: UploadFile = File(..., description="Candidate's CV in PDF format"),
    project_report_file: UploadFile = File(..., description="Candidate's Project Report in PDF format")
):
    """
    Menerima file CV dan Laporan Proyek, menyimpannya, dan mengembalikan ID unik.
    """
    uploaded_files = []

    files_to_process = {
        "cv": cv_file,
        "project_report": project_report_file
    }

    for doc_type, file in files_to_process.items():
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        document_paths[file_id] = file_path
        uploaded_files.append(schemas.UploadResponseItem(
            file_name=file.filename,
            document_id=file_id,
            document_type=doc_type
        ))

    return schemas.UploadResponse(message="Files uploaded successfully", files=uploaded_files)

@app.post("/evaluate", response_model=schemas.EvaluateResponse, status_code=202)
def evaluate_candidate(request: schemas.EvaluateRequest):
    """
    Memicu pipeline evaluasi AI secara asinkron.
    """
    cv_path = document_paths.get(request.cv_document_id)
    report_path = document_paths.get(request.project_report_id)

    if not cv_path or not report_path:
        raise HTTPException(status_code=404, detail="One or both document IDs not found.")

    job_id = str(uuid.uuid4())
    create_job(job_id)

    # Kirim tugas ke Celery untuk diproses di background
    tasks.process_evaluation.delay(
        job_id=job_id,
        cv_path=cv_path,
        report_path=report_path,
        job_title=request.job_title
    )

    return schemas.EvaluateResponse(id=job_id, status="queued")

@app.get("/result/{job_id}", response_model=schemas.GetResultResponse)
def get_evaluation_result(job_id: str):
    """
    Mengambil status dan hasil dari sebuah job evaluasi.
    """
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found.")

    response_data = {"id": job_id, "status": job["status"]}
    
    if job["status"] == "completed":
        response_data["result"] = job.get("result")
    elif job["status"] == "failed":
        # Ambil detail error dari hasil jika ada
        error_detail = job.get("result", {}).get("error", "An unknown error occurred.")
        response_data["error"] = error_detail

    return response_data