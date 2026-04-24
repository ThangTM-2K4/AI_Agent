import httpx

from app.core.config import settings


class AIReportService:
    @staticmethod
    def _fallback_report(payload: dict, error_detail: str | None = None) -> str:
        recommendations = payload.get("recommendations") or []
        rec_text = "\n".join([f"- {item}" for item in recommendations]) if recommendations else "- Chua co goi y chi tiet."
        unfinished_courses = payload.get("unfinished_courses") or []
        x_text = ", ".join(unfinished_courses) if unfinished_courses else "Không có"
        average_score = payload.get("average_score")
        if average_score is None:
            average_score = payload.get("avg_score")

        gpa_4 = payload.get("gpa_4")
        if gpa_4 is None:
            gpa_4 = payload.get("gpa")

        gpa_display = payload.get("gpa_display") or f"GPA: {average_score if average_score is not None else 0} ({gpa_4 if gpa_4 is not None else 0})"

        report = (
            "Tổng quan:\n"
            f"Sinh viên {payload.get('full_name')} ({payload.get('student_code')}) có {gpa_display}, "
            f"điểm trung bình {average_score if average_score is not None else 0}, {len(payload.get('failed_courses') or [])} môn dưới 5, "
            f"tín chỉ hoàn thành {payload.get('completed_credits')}. Mức rủi ro: {payload.get('risk_level')}.\n\n"
            "Xu hướng:\n"
            f"Xu hướng: {payload.get('trend')} ({payload.get('delta')} điểm).\n"
            f"Giai đoạn yếu: {payload.get('weak_phase')}. Giai đoạn cải thiện: {payload.get('improve_phase')}.\n\n"
            "Cảnh báo rủi ro:\n"
            f"Môn dưới 5: {', '.join(payload.get('failed_courses') or []) or 'Không có'}.\n"
            f"Môn chưa hoàn thành (X): {x_text}.\n"
            f"KPI % A/B: {payload.get('ab_rate')}%. % C/D: {payload.get('cd_rate')}%. \n"
            f"Nhận định: {payload.get('insight')}\n\n"
            "Kế hoạch cải thiện 4 tuần:\n"
            f"{rec_text}"
        )

        return report

    @staticmethod
    async def generate_report(payload: dict) -> str:
        if not settings.xai_api_key:
            return (
                "Chưa cấu hình XAI_API_KEY. Vui lòng cập nhật file .env để hệ thống gọi Grok API và tạo báo cáo AI chi tiết."
            )

        if settings.xai_api_key.startswith("gsk_") and "x.ai" in settings.xai_base_url:
            return AIReportService._fallback_report(payload)

        prompt = (
                "Bạn là AI Agent phân tích học tập sinh viên. Dữ liệu đầu vào gồm kết quả điểm, xu hướng, rủi ro và hành vi học tập. "
                "Hãy viết báo cáo ngắn gọn, rõ ràng bằng tiếng Việt, gồm 4 phần: Tổng quan, Đánh giá xu hướng, Cảnh báo rủi ro, "
                "Kế hoạch cải thiện trong 4 tuần. Nếu rủi ro cao, đưa ra cảnh báo mạnh. "
                "Trong phần Cảnh báo rủi ro, liệt kê rõ môn dưới 5.0, môn chưa hoàn thành (X), KPI và nhận định cuối.\n\n"
            f"Dữ liệu: {payload}"
        )

        url = f"{settings.xai_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.xai_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": settings.xai_model,
            "messages": [
                {"role": "system", "content": "Ban la tro ly hoc tap cho truong dai hoc."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(url, headers=headers, json=body)
                response.raise_for_status()
                data = response.json()

            return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as exc:
            detail = f"Grok API lỗi {exc.response.status_code}: {exc.response.text[:300]}"
            return AIReportService._fallback_report(payload, detail)
        except httpx.RequestError as exc:
            return AIReportService._fallback_report(payload, f"Không kết nối được Grok API: {exc}")
        except Exception as exc:  # pragma: no cover
            return AIReportService._fallback_report(payload, f"Lỗi AI không xác định: {exc}")
