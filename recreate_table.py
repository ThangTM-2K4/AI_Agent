from app.core.database import engine
from app.models.student import Base, CourseResult

# Drop and recreate CourseResult table
print("Dropping course_results table...")
Base.metadata.drop_all(engine, tables=[CourseResult.__table__])

print("Creating course_results table with grade field...")
Base.metadata.create_all(engine, tables=[CourseResult.__table__])

print("Done!")
