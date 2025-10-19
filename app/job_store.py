# /app/job_store.py

from typing import Dict, Any

# Ini akan bertindak sebagai database in-memory.
jobs: Dict[str, Dict[str, Any]] = {}
document_paths: dict[str, str] = {} 

def create_job(job_id: str):
    """Membuat entri job baru dengan status 'queued'."""
    jobs[job_id] = {"status": "queued", "result": None}

def get_job_status(job_id: str) -> Dict[str, Any] | None:
    """Mengambil status dan hasil dari sebuah job."""
    return jobs.get(job_id)

def update_job_status(job_id: str, status: str, result: Dict[str, Any] = None):
    """Memperbarui status dan hasil dari sebuah job."""
    if job_id in jobs:
        jobs[job_id]["status"] = status
        if result:
            jobs[job_id]["result"] = result
