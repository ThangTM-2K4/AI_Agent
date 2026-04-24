"""
Script để tạo test data cho sinh viên 22103024 với D1 < 5 nhưng D2 > 5 (để test logic cứu môn).
"""
from app.core.database import SessionLocal
from app.models.student import Student, CourseResult

db = SessionLocal()

try:
    # Xóa dữ liệu cũ nếu có
    existing = db.query(Student).filter(Student.student_code == "22103024").first()
    if existing:
        db.query(CourseResult).filter(CourseResult.student_id == existing.id).delete()
        db.delete(existing)
        db.commit()
    
    # Tạo sinh viên
    student = Student(
        student_code="22103024",
        full_name="Nguyễn Văn A",
        class_name="CNTT-K17"
    )
    db.add(student)
    db.flush()
    
    # Tạo các môn học
    courses = [
        # Môn bình thường: D1=8, D2=8 -> không phải dưới 5
        CourseResult(
            student_id=student.id,
            semester="2024-1",
            course_code="CS101",
            course_name="Nhập môn lập trình",
            credits=3,
            score=8.0,
            score_d1=8.0,
            score_d2=8.0,
            grade="A"
        ),
        # Môn khó: D1=3, D2=9 -> D2 cứu được, không phải dưới 5
        CourseResult(
            student_id=student.id,
            semester="2024-1",
            course_code="CS102",
            course_name="Cơ sở dữ liệu",
            credits=3,
            score=9.0,  # D2 ưu tiên, nên score=9
            score_d1=3.0,  # D1 < 5 nhưng D2 cứu
            score_d2=9.0,
            grade="A"
        ),
        # Môn thực sự dưới 5: D1=4, D2=3 -> tính là dưới 5
        CourseResult(
            student_id=student.id,
            semester="2024-1",
            course_code="CS103",
            course_name="Thực hành Lập trình hướng đối tượng",
            credits=2,
            score=3.0,
            score_d1=4.0,
            score_d2=3.0,
            grade="F"
        ),
        # Môn bình thường
        CourseResult(
            student_id=student.id,
            semester="2024-1",
            course_code="CS104",
            course_name="Lập trình web",
            credits=4,
            score=7.5,
            score_d1=7.5,
            score_d2=7.5,
            grade="B"
        ),
        # Môn X (chưa hoàn thành)
        CourseResult(
            student_id=student.id,
            semester="2024-1",
            course_code="CS105",
            course_name="Khóa luận tốt nghiệp",
            credits=6,
            score=0.0,
            score_d1=None,
            score_d2=None,
            grade="X"
        ),
    ]
    
    db.add_all(courses)
    db.commit()
    
    print("✅ Test data created successfully!")
    print(f"Student: 22103024 - Nguyễn Văn A")
    print(f"Courses: {len(courses)}")
    
finally:
    db.close()
