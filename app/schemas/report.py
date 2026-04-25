from typing import Optional

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    student_code: Optional[str] = Field(default=None, max_length=20)


class ReportResponse(BaseModel):
    student_code: str
    full_name: str
    class_name: Optional[str]
    status: str
    average_score: float
    gpa_4: float
    gpa_display: str
    total_failed_subjects: int
    summary: str
    risk_level: str
    failed_courses: list[str]
    retake_courses: list[str]
    unfinished_courses: list[str]
    completed_credits: int
    ab_rate: float
    cd_rate: float
    trend: str
    delta: float
    weak_phase: str
    improve_phase: str
    insight: str
    recommendations: list[str]
    ai_report: str
