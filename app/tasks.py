import os

from .config import settings
from .ai_utils import (
    parse_pdf,
    run_cv_evaluation,
    run_project_evaluation,
    run_final_summary,
)
from .job_store import update_job_status

def process_evaluation_sync(job_id: str, cv_path: str, report_path: str, job_title: str):
    """
    Tugas Celery yang menjalankan seluruh pipeline evaluasi AI secara asinkron.
    """
    print(f"Starting evaluation for job_id: {job_id}")
    try:
        # Update status menjadi 'processing'
        update_job_status(job_id, "processing")

        # 1. Parse dokumen PDF yang diunggah
        cv_text = parse_pdf(cv_path)
        report_text = parse_pdf(report_path)

        if not cv_text or not report_text:
            raise ValueError("Failed to parse one or both PDF documents.")

        # 2. Jalankan evaluasi CV
        cv_result = run_cv_evaluation(cv_text, job_title)

        # 3. Jalankan evaluasi Proyek
        project_result = run_project_evaluation(report_text)

        # 4. Buat ringkasan akhir
        summary_result = run_final_summary(
            cv_feedback=cv_result.get("cv_feedback", ""),
            project_feedback=project_result.get("project_feedback", "")
        )

        # 5. Gabungkan semua hasil
        final_result = {
            **cv_result,
            **project_result,
            **summary_result
        }
        
        # 6. Perbarui status menjadi 'completed' dengan hasil akhir
        update_job_status(job_id, "completed", final_result)
        print(f"Evaluation completed successfully for job_id: {job_id}")

    except Exception as e:
        print(f"Error during evaluation for job_id {job_id}: {e}")
        # Jika terjadi error, tandai job sebagai 'failed'
        update_job_status(job_id, "failed", {"error": str(e)})
    finally:
        # Opsional: Hapus file yang diunggah setelah selesai diproses
        if os.path.exists(cv_path):
            os.remove(cv_path)
        if os.path.exists(report_path):
            os.remove(report_path)