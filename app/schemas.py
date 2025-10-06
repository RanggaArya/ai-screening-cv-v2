from pydantic import BaseModel
from typing import List, Optional

# --- Skema untuk /upload ---
class UploadResponseItem(BaseModel):
    file_name: str
    document_id: str
    document_type: str

class UploadResponse(BaseModel):
    message: str
    files: List[UploadResponseItem]

# --- Skema untuk /evaluate ---
class EvaluateRequest(BaseModel):
    job_title: str
    cv_document_id: str
    project_report_id: str

class EvaluateResponse(BaseModel):
    id: str
    status: str

# --- Skema untuk /result/{id} ---
class EvaluationResult(BaseModel):
    cv_match_rate: float
    cv_feedback: str
    project_score: float
    project_feedback: str
    overall_summary: str

class GetResultResponse(BaseModel):
    id: str
    status: str
    result: Optional[EvaluationResult] = None
    error: Optional[str] = None