from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
import re

from app.core.database import get_db
from app.repositories.student_repository import StudentRepository
from app.schemas.import_result import ImportResult
from app.schemas.report import ReportRequest, ReportResponse
from app.services.excel_import_service import ExcelImportService
from app.services.ai_report_service import AIReportService
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1", tags=["report"])


@router.post("/report", response_model=ReportResponse)
async def build_report(request: ReportRequest, db: Session = Depends(get_db)):
    if not request.student_code and not request.full_name:
        raise HTTPException(status_code=400, detail="Vui lòng nhập mã số sinh viên hoặc họ tên.")

    repo = StudentRepository(db)
    student = repo.get_student(request.student_code, request.full_name)
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


@router.post("/import-excel", response_model=ImportResult)
async def import_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = (file.filename or "").lower()
    if not filename.endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file Excel .xlsx hoặc .xlsm.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="File Excel rỗng.")

    try:
        service = ExcelImportService(db)
        result = service.import_workbook(file_bytes)
        return ImportResult(**result)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        import traceback

        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi: {exc}") from exc
