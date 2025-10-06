import redis
import json
from typing import Dict, Any

# --- Konfigurasi ---
# Menghubungkan ke server Redis yang sama dengan yang digunakan Celery
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

def create_job(job_id: str):
    """Membuat entri job baru di Redis dengan status 'queued'."""
    initial_data = {"status": "queued", "result": None}
    # Simpan sebagai string JSON
    redis_client.set(job_id, json.dumps(initial_data))

def get_job_status(job_id: str) -> Dict[str, Any] | None:
    """Mengambil status dan hasil dari sebuah job di Redis."""
    job_data_json = redis_client.get(job_id)
    if job_data_json:
        # Ubah string JSON kembali menjadi dictionary Python
        return json.loads(job_data_json)
    return None

def update_job_status(job_id: str, status: str, result: Dict[str, Any] = None):
    """Memperbarui status dan hasil dari sebuah job di Redis."""
    # Ambil data yang ada
    job_data = get_job_status(job_id)
    if job_data:
        # Perbarui datanya
        job_data["status"] = status
        if result:
            job_data["result"] = result
        # Simpan kembali ke Redis
        redis_client.set(job_id, json.dumps(job_data))