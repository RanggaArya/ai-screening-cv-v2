# /app/tasks.py
import os
from .ai_utils import parse_pdf, run_cv_evaluation, run_project_evaluation, run_final_summary
from .job_store import update_job_status

def process_evaluation_sync(job_id: str, cv_path: str, report_path: str, job_title: str):
    """
    Fungsi yang menjalankan seluruh pipeline evaluasi AI.
    """
    print(f"Starting evaluation for job_id: {job_id}")
    try:
        update_job_status(job_id, "processing")

        cv_text = parse_pdf(cv_path)
        report_text = parse_pdf(report_path)

        if not cv_text or not report_text:
            raise ValueError("Failed to parse one or both PDF documents.")

        cv_result = run_cv_evaluation(cv_text, job_title)
        project_result = run_project_evaluation(report_text)
        summary_result = run_final_summary(
            cv_feedback=cv_result.get("cv_feedback", ""),
            project_feedback=project_result.get("project_feedback", "")
        )

        final_result = {**cv_result, **project_result, **summary_result}
        update_job_status(job_id, "completed", final_result)
        print(f"Evaluation completed successfully for job_id: {job_id}")

    except Exception as e:
        print(f"Error during evaluation for job_id {job_id}: {e}")
        update_job_status(job_id, "failed", {"error": str(e)})
    finally:
        if os.path.exists(cv_path):
            os.remove(cv_path)
        if os.path.exists(report_path):
            os.remove(report_path)
