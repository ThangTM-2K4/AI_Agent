import math
import re
from datetime import date, datetime
from statistics import mean

from app.models.student import CourseResult, LearningActivity


def _normalize_text_for_match(value: object) -> str:
    import re
    import unicodedata

    text = str(value or "").lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = text.replace("đ", "d")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _format_semester_label(semester_value: str) -> str:
    import re

    text = str(semester_value or "").strip()
    if not text:
        return "N/A"

    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    if len(numbers) >= 2:
        try:
            year = int(float(numbers[0]))
            semester = int(float(numbers[1]))
            return f"Kỳ {semester} - {year}"
        except Exception:
            return text

    return text


class AnalyticsService:
    VALID_GRADES = {"A", "B", "C", "D", "F"}

    # =========================
    # INTERNAL HELPERS
    # =========================

    @staticmethod
    def _grade_subjects(subjects: list[dict]) -> list[dict]:
        """Lọc các môn có điểm chữ hợp lệ (A/B/C/D/F)."""
        grade_subjects: list[dict] = []
        for s in subjects:
            grade = str(s.get("grade") or "").strip().upper()
            if grade in {"A", "B", "C", "D", "F"}:
                grade_subjects.append({"name": s.get("name"), "grade": grade})
        return grade_subjects

    @staticmethod
    def _format_number(value: float) -> str:
        text = f"{value:.2f}".rstrip("0").rstrip(".")
        return text or "0"

    @staticmethod
    def normalize_score_value(value: object) -> float | None:
        """Chuẩn hóa một giá trị điểm về khoảng 0-10, trả về None nếu không thể dùng."""
        if value is None or isinstance(value, bool):
            return None

        if isinstance(value, (date, datetime)):
            return None

        if isinstance(value, (int, float)):
            number = float(value)
        else:
            text = str(value).strip()
            if not text:
                return None

            text = text.replace(",", ".")
            try:
                number = float(text)
            except ValueError:
                digits = re.sub(r"\D", "", text)
                if not digits:
                    return None
                number = float(digits)

        if not math.isfinite(number) or number < 0:
            return None

        if number <= 10:
            return round(number, 2)

        digits = re.sub(r"\D", "", str(int(abs(number))))
        if not digits:
            return None

        if len(digits) >= 2:
            normalized = float(f"{digits[0]}.{digits[1]}")
        else:
            normalized = float(digits[0])

        return round(min(normalized, 10.0), 2)

    @staticmethod
    def _score_to_gpa_4(score: float) -> float:
        if score >= 8.5:
            return 4.0
        if score >= 7.0:
            return 3.0
        if score >= 5.5:
            return 2.0
        if score >= 4.0:
            return 1.0
        return 0.0

    @staticmethod
    def clean_subjects(subjects: list[dict]) -> list[dict]:
        """Làm sạch danh sách môn học để dùng cho hiển thị và tính toán."""
        cleaned: list[dict] = []

        for sub in subjects:
            name = str(sub.get("name") or "").strip()
            if not name:
                continue

            grade = str(sub.get("grade") or "").strip().upper()
            credit = sub.get("credit")
            try:
                credit_int = int(credit)
            except Exception:
                credit_int = None

            score_d1 = AnalyticsService.normalize_score_value(sub.get("score_d1"))
            score_d2 = AnalyticsService.normalize_score_value(sub.get("score_d2"))
            effective_score = score_d2 if score_d2 is not None else score_d1
            if effective_score is None:
                effective_score = AnalyticsService.normalize_score_value(sub.get("score"))

            if credit_int is None or credit_int <= 0:
                credit_int = 0

            if grade != "X" and (effective_score is None or credit_int <= 0):
                continue

            cleaned.append(
                {
                    "name": name,
                    "score": effective_score,
                    "score_d1": score_d1,
                    "score_d2": score_d2,
                    "credit": credit_int,
                    "grade": grade,
                    "semester": sub.get("semester", ""),
                }
            )

        return cleaned

    @staticmethod
    def aggregate_unfinished_and_credits_from_df(df) -> tuple[int, float]:
        """
        Tính số môn chưa hoàn thành và tổng tín chỉ từ DataFrame.

        Yêu cầu cột:
        - ĐChữ: điểm chữ
        - TChỉ: số tín chỉ
        """
        if "ĐChữ" not in df.columns or "TChỉ" not in df.columns:
            raise ValueError("DataFrame phải có cột 'ĐChữ' và 'TChỉ'.")

        grade_series = df["ĐChữ"].astype(str).str.strip().str.upper()
        credit_series = (
            df["TChỉ"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.extract(r"([0-9]+(?:\.[0-9]+)?)", expand=False)
            .fillna("0")
            .astype(float)
        )

        total_failed_subjects = int((grade_series == "X").sum())
        total_credits = float(credit_series[grade_series != "X"].sum())

        return total_failed_subjects, total_credits

    @staticmethod
    def _is_failed(subject: dict) -> bool:
        """
        Xác định môn học có bị rớt hay không.

        Logic:
        - Nếu grade == "F"   → rớt (chính xác nhất, ưu tiên tuyệt đối).
        - Nếu grade == "X"   → chưa hoàn thành, KHÔNG tính là rớt.
        - Nếu grade == "P"   → đạt (pass/fail system), KHÔNG tính là rớt.
        - Nếu grade hợp lệ khác (A/B/C/D) → đã qua, KHÔNG tính là rớt.
        - Nếu không có grade → fallback: score < 5.
        """
        grade = str(subject.get("grade") or "").upper()
        score = subject.get("score")

        if grade == "X":
            return False
        if grade == "P":
            return False
        if grade == "F":
            return True
        if grade in {"A", "B", "C", "D"}:
            return False
        # Không có điểm chữ hợp lệ → dùng điểm số
        return score is not None and score < 5

    # =========================
    # CONVERT DATA
    # =========================

    @staticmethod
    def to_subjects(course_results: list[CourseResult]) -> list[dict]:
        """Chuyển danh sách CourseResult sang list[dict] chuẩn hoá."""
        subjects: list[dict] = []

        for item in course_results:
            score = None
            credit = None
            score_d1 = None
            score_d2 = None

            try:
                if item.score is not None:
                    score = float(item.score)
            except Exception:
                score = None

            try:
                if item.credits is not None:
                    credit = int(item.credits)
            except Exception:
                credit = None

            try:
                if getattr(item, "score_d1", None) is not None:
                    score_d1 = float(item.score_d1)
            except Exception:
                score_d1 = None

            try:
                if getattr(item, "score_d2", None) is not None:
                    score_d2 = float(item.score_d2)
            except Exception:
                score_d2 = None

            # Ưu tiên letter_grade, fallback sang grade để không mất dữ liệu điểm chữ.
            grade = str(
                getattr(item, "letter_grade", None)
                or getattr(item, "grade", "")
            ).strip().upper()

            subjects.append(
                {
                    "name": item.course_name,
                    "score": score,
                    "score_d1": score_d1,
                    "score_d2": score_d2,
                    "credit": credit,
                    "grade": grade,
                    "semester": str(getattr(item, "semester", "") or ""),
                }
            )

        return subjects

    # =========================
    # FILTER VALID SUBJECTS
    # =========================

    @staticmethod
    def _valid_subjects(subjects: list[dict]) -> list[dict]:
        """
        Lọc các môn hợp lệ để tính GPA / KPI.

        Loại trừ:
        - Môn thiếu tên, điểm số, hoặc tín chỉ.
        - Thực tập nghề nghiệp / Khóa luận tốt nghiệp.
        - Điểm chữ P (pass/fail) và X (chưa hoàn thành).
        - Điểm chữ không hợp lệ (không nằm trong A/B/C/D/F và không rỗng).
        - Tín chỉ <= 0.
        """
        valid: list[dict] = []

        for sub in subjects:
            name = str(sub.get("name") or "").strip()
            score = sub.get("score")
            credit = sub.get("credit")
            grade = str(sub.get("grade") or "").upper()

            if not name or score is None or credit is None:
                continue

            # Không tính các học phần đặc thù vào GPA/KPI.
            normalized_name = _normalize_text_for_match(name)
            if "thuc tap" in normalized_name or "khoa luan" in normalized_name:
                continue

            # Loại P (pass/fail) và X (chưa hoàn thành) — không tính GPA.
            if grade in {"P", "X"}:
                continue

            # Loại điểm chữ không thuộc tập hợp hợp lệ (nếu có giá trị).
            if grade and grade not in AnalyticsService.VALID_GRADES:
                continue

            try:
                score = float(score)
                credit = int(credit)
            except Exception:
                continue

            if credit <= 0:
                continue

            valid.append(
                {
                    "name": name,
                    "score": score,
                    "credit": credit,
                    "grade": grade,
                    "semester": sub.get("semester", ""),
                }
            )

        return valid

    # =========================
    # LIST COURSES
    # =========================

    @staticmethod
    def list_failed_courses(subjects: list[dict]) -> list[str]:
        """
        Trả về danh sách môn dưới 5 điểm theo điểm hiệu lực cuối cùng.

        Quy tắc:
        - Nếu có D2 thì dùng D2.
        - Nếu D2 trống thì dùng D1.
        - Nếu không có cả D1/D2 thì fallback sang score đã lưu trong DB.
        - Môn dưới 5 khi điểm hiệu lực < 5.
        """
        cleaned = AnalyticsService.clean_subjects(subjects)
        failed = []
        for s in cleaned:
            if not s.get("name"):
                continue

            if str(s.get("grade") or "").upper() == "X":
                continue

            effective_score = s.get("score")

            if effective_score is not None and effective_score < 5:
                failed.append(s["name"])

        return failed

    @staticmethod
    def list_unfinished_courses(subjects: list[dict]) -> list[str]:
        """Trả về danh sách môn chưa hoàn thành (grade == X)."""
        cleaned = AnalyticsService.clean_subjects(subjects)
        return [
            s["name"]
            for s in cleaned
            if str(s.get("grade") or "").upper() == "X"
        ]

    @staticmethod
    def list_retake_courses(subjects: list[dict]) -> list[str]:
        """Trả về danh sách môn phải học lại (grade == F)."""
        cleaned = AnalyticsService.clean_subjects(subjects)
        return [
            s["name"]
            for s in cleaned
            if str(s.get("grade") or "").upper() == "F"
        ]

    @staticmethod
    def count_unfinished_courses(subjects: list[dict]) -> int:
        """Đếm số môn chưa hoàn thành (grade == X)."""
        return len(AnalyticsService.list_unfinished_courses(subjects))

    # =========================
    # CALCULATION
    # =========================

    @staticmethod
    def calculate_gpa(subjects: list[dict]) -> float:
        """Tính GPA hệ 4.0 theo trọng số tín chỉ."""
        valid = AnalyticsService._valid_subjects(AnalyticsService.clean_subjects(subjects))

        total_credit = sum(s["credit"] for s in valid)
        if total_credit == 0:
            return 0.0

        weighted_sum = sum(AnalyticsService._score_to_gpa_4(s["score"]) * s["credit"] for s in valid)
        return round(weighted_sum / total_credit, 2)

    @staticmethod
    def calculate_avg(subjects: list[dict]) -> float:
        """Tính điểm trung bình hệ 10 có trọng số tín chỉ."""
        valid = AnalyticsService._valid_subjects(AnalyticsService.clean_subjects(subjects))
        if not valid:
            return 0.0

        total_credit = sum(s["credit"] for s in valid)
        if total_credit == 0:
            return 0.0

        weighted_sum = sum(s["score"] * s["credit"] for s in valid)
        return round(weighted_sum / total_credit, 2)

    @staticmethod
    def format_gpa_display(avg_score: float, gpa_4: float) -> str:
        return f"GPA: {AnalyticsService._format_number(avg_score)} ({AnalyticsService._format_number(gpa_4)})"

    @staticmethod
    def count_failed(subjects: list[dict]) -> int:
        """Đếm số môn bị rớt."""
        return len(AnalyticsService.list_failed_courses(subjects))

    # =========================
    # KPI
    # =========================

    @staticmethod
    def calculate_completed_credits(subjects: list[dict]) -> int:
        """Tổng tín chỉ, loại trừ các môn có grade == X."""
        cleaned = AnalyticsService.clean_subjects(subjects)
        total = 0

        for sub in cleaned:
            grade = str(sub.get("grade") or "").upper()
            if grade == "X":
                continue

            try:
                credit = int(sub.get("credit") or 0)
            except Exception:
                continue

            total += credit

        return total

    @staticmethod
    def calculate_ab_rate(subjects: list[dict]) -> float:
        """Tỉ lệ % môn đạt A hoặc B."""
        grade_subjects = AnalyticsService._grade_subjects(AnalyticsService.clean_subjects(subjects))
        if not grade_subjects:
            return 0.0

        ab_count = sum(1 for s in grade_subjects if s["grade"] in {"A", "B"})
        return round((ab_count * 100) / len(grade_subjects), 2)

    @staticmethod
    def calculate_fail_rate(subjects: list[dict]) -> float:
        """
        Tỉ lệ % môn bị rớt trên tổng môn hợp lệ (đã qua _valid_subjects).

        Dùng _is_failed thay vì score < 5 để tránh tính nhầm môn D thi lại.
        """
        valid = AnalyticsService._valid_subjects(AnalyticsService.clean_subjects(subjects))
        if not valid:
            return 0.0

        fail_count = sum(1 for s in valid if AnalyticsService._is_failed(s))
        return round((fail_count * 100) / len(valid), 2)

    @staticmethod
    def calculate_cd_rate(subjects: list[dict]) -> float:
        """Tỉ lệ % môn đạt C hoặc D."""
        grade_subjects = AnalyticsService._grade_subjects(AnalyticsService.clean_subjects(subjects))
        if not grade_subjects:
            return 0.0

        cd_count = sum(1 for s in grade_subjects if s["grade"] in {"C", "D"})
        return round((cd_count * 100) / len(grade_subjects), 2)

    # =========================
    # RISK
    # =========================

    @staticmethod
    def risk_level_by_gpa(gpa: float, failed: int) -> str:
        """
        Xác định mức rủi ro học tập dựa trên GPA và số môn rớt.

        HIGH   : GPA < 5.0  HOẶC  rớt >= 5 môn
        MEDIUM : GPA < 6.5  HOẶC  rớt >= 2 môn
        LOW    : còn lại
        """
        if gpa < 5.0 or failed >= 5:
            return "HIGH"
        if gpa < 6.5 or failed >= 2:
            return "MEDIUM"
        return "LOW"

    # =========================
    # TREND
    # =========================

    @staticmethod
    def trend_by_semester(scores_by_semester: dict[str, list[float]]) -> dict:
        """
        Phân tích xu hướng điểm theo kỳ học.

        Trả về:
        - trend       : mô tả xu hướng (Tăng mạnh / Giảm / Ổn định).
        - delta       : chênh lệch điểm trung bình kỳ cuối so với kỳ đầu.
        - weak_phase  : kỳ học yếu nhất (điểm TB thấp nhất).
        - improve_phase: kỳ học tốt nhất (điểm TB cao nhất).
        """
        if len(scores_by_semester) < 2:
            return {
                "trend": "Không đủ dữ liệu",
                "delta": 0.0,
                "weak_phase": "N/A",
                "improve_phase": "N/A",
            }

        semesters = sorted(scores_by_semester.keys())
        avg_by_semester = {
            sem: mean(scores) for sem, scores in scores_by_semester.items()
        }

        first_avg = avg_by_semester[semesters[0]]
        last_avg = avg_by_semester[semesters[-1]]
        delta = round(last_avg - first_avg, 2)

        if delta > 1:
            trend = "Tăng mạnh"
        elif delta < -1:
            trend = "Giảm"
        else:
            trend = "Ổn định"

        weak_sem = min(avg_by_semester, key=avg_by_semester.__getitem__)
        best_sem = max(avg_by_semester, key=avg_by_semester.__getitem__)

        return {
            "trend": trend,
            "delta": delta,
            "weak_phase": _format_semester_label(weak_sem),
            "improve_phase": _format_semester_label(best_sem),
        }

    # =========================
    # FINAL RISK
    # =========================

    @staticmethod
    def risk_level(
        course_results: list[CourseResult],
        activities: list[LearningActivity],
    ) -> str:
        """Tính mức rủi ro tổng hợp từ kết quả học tập."""
        subjects = AnalyticsService.to_subjects(course_results)

        gpa = AnalyticsService.calculate_avg(subjects)
        failed = AnalyticsService.count_failed(subjects)

        return AnalyticsService.risk_level_by_gpa(gpa, failed)

    # =========================
    # RECOMMENDATIONS
    # =========================

    @staticmethod
    def recommendations(risk_level: str, failed_courses: list[str]) -> list[str]:
        """
        Sinh danh sách khuyến nghị học tập dựa trên mức rủi ro.

        HIGH   → kế hoạch khắc phục khẩn cấp.
        MEDIUM → kế hoạch cải thiện.
        LOW    → kế hoạch duy trì và nâng cao.
        """
        failed_text = (
            ", ".join(failed_courses) if failed_courses else "Không có môn dưới 5"
        )

        if risk_level == "HIGH":
            return [
                f" Ưu tiên ôn tập ngay các môn: {failed_text}",
                " Tuần 1–2: Hệ thống lại kiến thức nền từng môn yếu",
                " Tuần 3–4: Luyện đề + bài tập thực hành mỗi ngày",
                " Hằng ngày: Học tối thiểu 3–4 giờ",
                " Liên hệ giảng viên hoặc trợ lý học tập để được hỗ trợ",
                " Kiểm tra tiến độ mỗi cuối tuần, điều chỉnh kế hoạch kịp thời",
            ]

        if risk_level == "MEDIUM":
            return [
                f" Tập trung cải thiện các môn yếu: {failed_text}",
                " Tuần 1–2: Ôn lại lý thuyết và bài tập các môn có điểm thấp",
                " Tuần 3–4: Làm đề thi thử, rèn kỹ năng làm bài",
                " Hằng ngày: Học ≥ 2 giờ, review bài cũ 30 phút",
                " Đặt mục tiêu cụ thể cho từng môn trong kỳ tới",
            ]

        # LOW
        return [
            " Kết quả tốt! Duy trì và phấn đấu lên cao hơn",
            " Mở rộng kiến thức chuyên sâu hoặc học thêm kỹ năng mới",
            " Hằng ngày: Học ≥ 2 giờ, đọc thêm tài liệu tham khảo",
            " Cân nhắc tham gia nghiên cứu khoa học hoặc dự án thực tế",
        ]