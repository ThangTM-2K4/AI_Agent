from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
import re

from app.core.database import get_db
from app.core.config import settings
from app.repositories.student_repository import StudentRepository
from app.schemas.import_result import ImportResult
from app.schemas.report import ReportRequest, ReportResponse
from app.services.excel_import_service import ExcelImportService
from app.services.ai_report_service import AIReportService
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1", tags=["report"])
public_router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


def _is_data_loaded(request: Request) -> bool:
    return bool(getattr(request.app.state, "data_loaded", False))


def _get_current_user(request: Request) -> Optional[dict]:
    return request.session.get("user")


def _require_teacher(request: Request) -> dict:
    user = _get_current_user(request)
    if not user or user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Chỉ giáo viên mới có quyền thực hiện chức năng này.")
    return user


async def _build_report(student_code: Optional[str], db: Session) -> ReportResponse:
    if not student_code:
        raise HTTPException(status_code=400, detail="Vui lòng nhập mã số sinh viên.")

    repo = StudentRepository(db)
    student = repo.get_student(student_code, None)
    if not student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên.")

    display_full_name = student.full_name
    display_class_name = student.class_name
    legacy_match = re.search(r"^(.*?)\s*-\s*lớp\s*:\s*(.+)$", str(student.full_name or ""), flags=re.IGNORECASE)
    if legacy_match:
        display_full_name = legacy_match.group(1).strip() or student.full_name
        if not display_class_name:
            display_class_name = legacy_match.group(2).strip()
    display_status = "Đang học"

    course_results = repo.get_course_results(student.id)
    activities = repo.get_learning_activities(student.id)
    semesters = repo.group_scores_by_semester(course_results)
    subjects = AnalyticsService.to_subjects(course_results)
    normalized_subjects = AnalyticsService.clean_subjects(subjects)

    avg_score = AnalyticsService.calculate_avg(normalized_subjects)
    gpa_4 = AnalyticsService.calculate_gpa(normalized_subjects)
    gpa_display = AnalyticsService.format_gpa_display(avg_score, gpa_4)
    failed_courses = AnalyticsService.list_failed_courses(normalized_subjects)
    retake_courses = AnalyticsService.list_retake_courses(normalized_subjects)
    unfinished_courses = AnalyticsService.list_unfinished_courses(normalized_subjects)
    total_failed_subjects = AnalyticsService.count_unfinished_courses(normalized_subjects)
    fail_count = len(failed_courses)
    completed_credits = AnalyticsService.calculate_completed_credits(normalized_subjects)
    ab_rate = AnalyticsService.calculate_ab_rate(normalized_subjects)
    cd_rate = AnalyticsService.calculate_cd_rate(normalized_subjects)
    trend_info = AnalyticsService.trend_by_semester(semesters)
    risk = AnalyticsService.risk_level_by_gpa(avg_score, fail_count)
    recs = AnalyticsService.recommendations(risk, failed_courses)
    insight = "Sinh viên đang cải thiện rõ nhưng nền tảng trước đó còn yếu"

    prompt_data = {
        "student_code": student.student_code,
        "full_name": display_full_name,
        "class_name": display_class_name,
        "status": display_status,
        "gpa": gpa_4,
        "gpa_4": gpa_4,
        "average_score": avg_score,
        "avg_score": avg_score,
        "gpa_display": gpa_display,
        "failed_courses": failed_courses,
        "retake_courses": retake_courses,
        "unfinished_courses": unfinished_courses,
        "total_failed_subjects": total_failed_subjects,
        "trend": trend_info["trend"],
        "delta": trend_info["delta"],
        "weak_phase": trend_info["weak_phase"],
        "improve_phase": trend_info["improve_phase"],
        "risk_level": risk,
        "completed_credits": completed_credits,
        "ab_rate": ab_rate,
        "cd_rate": cd_rate,
        "insight": insight,
        "recommendations": recs,
        "subjects": normalized_subjects,
    }
    ai_text = await AIReportService.generate_report(prompt_data)

    summary = (
        f"GPA: {avg_score}, Avg: {avg_score}, Môn dưới 5: {len(failed_courses)}, Số môn chưa hoàn thành: {total_failed_subjects}, Tín chỉ: {completed_credits}"
    )

    return ReportResponse(
        student_code=student.student_code,
        full_name=display_full_name,
        class_name=display_class_name,
        status=display_status,
        average_score=avg_score,
        gpa_4=gpa_4,
        gpa_display=gpa_display,
        total_failed_subjects=total_failed_subjects,
        summary=summary,
        risk_level=risk,
        failed_courses=failed_courses,
        retake_courses=retake_courses,
        unfinished_courses=unfinished_courses,
        completed_credits=completed_credits,
        ab_rate=ab_rate,
        cd_rate=cd_rate,
        trend=trend_info["trend"],
        delta=float(trend_info["delta"]),
        weak_phase=str(trend_info["weak_phase"]),
        improve_phase=str(trend_info["improve_phase"]),
        insight=insight,
        recommendations=recs,
        ai_report=ai_text,
    )


@router.post("/report", response_model=ReportResponse)
async def build_report(request: ReportRequest, req: Request, db: Session = Depends(get_db)):
    if not _is_data_loaded(req):
        raise HTTPException(status_code=400, detail="Hệ thống chưa có dữ liệu. Vui lòng đợi giáo viên tải lên.")
    return await _build_report(request.student_code, db)


@router.post("/import-excel", response_model=ImportResult)
@public_router.post("/upload", response_model=ImportResult)
async def import_excel(req: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    _require_teacher(req)

    filename = (file.filename or "").lower()
    if not filename.endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file Excel .xlsx hoặc .xlsm.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="File Excel rỗng.")

    try:
        service = ExcelImportService(db)
        result = service.import_workbook(file_bytes)
        req.app.state.data_loaded = True
        return ImportResult(**result)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        import traceback

        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi: {exc}") from exc


@public_router.post("/login")
async def login(payload: LoginRequest, request: Request):
    email = payload.username.strip().lower()
    display_name = settings.teacher_accounts.get(email)
    if not display_name or payload.password != settings.teacher_default_password:
        raise HTTPException(status_code=401, detail="login failed")

    request.session["user"] = {
        "username": email,
        "display_name": display_name,
        "role": "teacher",
        "avatar": settings.teacher_avatar,
    }
    return {
        "authenticated": True,
        "role": "teacher",
        "display_name": display_name,
        "avatar": settings.teacher_avatar,
    }


@public_router.post("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return {"authenticated": False}


@public_router.get("/search", response_model=ReportResponse)
async def search_report(mssv: str, request: Request, db: Session = Depends(get_db)):
    if not _is_data_loaded(request):
        raise HTTPException(status_code=400, detail="Hệ thống chưa có dữ liệu. Vui lòng đợi giáo viên tải lên.")
    return await _build_report(mssv, db)


@public_router.get("/state")
async def system_state(request: Request):
    user = _get_current_user(request)
    return {
        "data_loaded": _is_data_loaded(request),
        "authenticated": bool(user),
        "user": user,
    }
