from sqlalchemy import Column, Date, Float, ForeignKey, Integer, Unicode
from sqlalchemy.orm import relationship

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(Unicode(20), unique=True, index=True, nullable=False)
    full_name = Column(Unicode(255), index=True, nullable=False)
    class_name = Column(Unicode(50), nullable=True)

    course_results = relationship("CourseResult", back_populates="student")
    activities = relationship("LearningActivity", back_populates="student")


class CourseResult(Base):
    __tablename__ = "course_results"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    semester = Column(Unicode(20), nullable=False)
    course_code = Column(Unicode(20), nullable=False)
    course_name = Column(Unicode(255), nullable=False)
    credits = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    score_d1 = Column(Float, nullable=True)  # D1 gốc
    score_d2 = Column(Float, nullable=True)  # D2 gốc
    grade = Column(Unicode(5), nullable=True)

    student = relationship("Student", back_populates="course_results")


class LearningActivity(Base):
    __tablename__ = "learning_activities"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    event_date = Column(Date, nullable=False)
    metric_name = Column(Unicode(50), nullable=False)
    metric_value = Column(Float, nullable=False)

    student = relationship("Student", back_populates="activities")
