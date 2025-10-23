import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import shutil

# Karena struktur Vercel, kita perlu menyesuaikan cara impor
from app import schemas, tasks
from app.job_store import create_job, get_job_status, document_paths
from app.ai_utils import parse_pdf, run_cv_evaluation, run_project_evaluation, run_final_summary

# Vercel menggunakan direktori /tmp untuk penyimpanan sementara
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="AI CV Evaluator API")

# Konfigurasi CORS agar frontend Anda bisa mengakses API ini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Izinkan semua origin (untuk kemudahan)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_files(
    cv_file: UploadFile = File(...),
    project_report_file: UploadFile = File(...)
):
    uploaded_files = []
    files_to_process = {"cv": cv_file, "project_report": project_report_file}

    for doc_type, file in files_to_process.items():
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        document_paths[file_id] = file_path
        uploaded_files.append(schemas.UploadResponseItem(
            file_name=file.filename, document_id=file_id, document_type=doc_type
        ))

    return schemas.UploadResponse(message="Files uploaded successfully", files=uploaded_files)


@app.post("/evaluate")
def evaluate_candidate(
    request: schemas.EvaluateRequest,
    background_tasks: BackgroundTasks
):
    cv_path = document_paths.get(request.cv_document_id)
    report_path = document_paths.get(request.project_report_id)

    if not cv_path or not report_path or not os.path.exists(cv_path) or not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="One or both document files not found on the server.")

    job_id = str(uuid.uuid4())
    create_job(job_id)

    background_tasks.add_task(
        tasks.process_evaluation_sync,
        job_id=job_id,
        cv_path=cv_path,
        report_path=report_path,
        job_title=request.job_title,
    )

    return schemas.EvaluateResponse(id=job_id, status="queued")


@app.get("/result/{job_id}")
def get_evaluation_result(job_id: str):
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found.")

    response_data = {"id": job_id, "status": job["status"]}
    
    if job["status"] == "completed":
        response_data["result"] = job.get("result")
    elif job["status"] == "failed":
        error_detail = job.get("result", {}).get("error", "An unknown error occurred.")
        response_data["error"] = error_detail

    return response_data

# Endpoint root untuk verifikasi
@app.get("/")
def read_root():
    return {"status": "Backend is running"}
