from collections import defaultdict
import re
import unicodedata

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.student import CourseResult, LearningActivity, Student


class StudentRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _normalize_text(value: str) -> str:
        text = (value or "").strip().lower()
        text = text.replace("đ", "d")
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        text = re.sub(r"\s+", " ", text)
        return text

    def get_student(self, student_code: str | None, full_name: str | None) -> Student | None:
        code = (student_code or "").strip()
        name = (full_name or "").strip()

        if not code and not name:
            return None

        # 1) Prefer exact student_code when provided.
        if code:
            by_code = self.db.execute(select(Student).where(Student.student_code == code)).scalars().first()
            if by_code is not None:
                return by_code

        # 2) Fallback to SQL name contains match.
        if name:
            by_name = self.db.execute(
                select(Student).where(func.lower(Student.full_name).like(f"%{name.lower()}%"))
            ).scalars().first()
            if by_name is not None:
                return by_name

            # 3) Final fallback for names entered without Vietnamese accents.
            normalized_target = self._normalize_text(name)
            all_students = self.db.execute(select(Student)).scalars().all()
            for student in all_students:
                if normalized_target in self._normalize_text(student.full_name or ""):
                    return student

        return None

    def get_course_results(self, student_id: int) -> list[CourseResult]:
        query = (
            select(CourseResult)
            .where(CourseResult.student_id == student_id)
            .order_by(CourseResult.semester.asc())
        )
        return list(self.db.execute(query).scalars().all())

    def get_learning_activities(self, student_id: int) -> list[LearningActivity]:
        query = (
            select(LearningActivity)
            .where(LearningActivity.student_id == student_id)
            .order_by(LearningActivity.event_date.asc())
        )
        return list(self.db.execute(query).scalars().all())

    @staticmethod
    def group_scores_by_semester(course_results: list[CourseResult]) -> dict[str, list[float]]:
        semesters = defaultdict(list)
        for item in course_results:
            semesters[item.semester].append(item.score)
        return dict(semesters)
