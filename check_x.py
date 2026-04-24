from app.core.database import SessionLocal
from app.models.student import CourseResult

db = SessionLocal()
results = db.query(CourseResult).filter(CourseResult.grade == 'X').all()
print(f'Found {len(results)} courses with grade X')
for r in results[:5]:
    print(f'  sid={r.student_id}, {r.course_name}, {r.grade}, score={r.score}')

# Also check total courses in DB
total = db.query(CourseResult).count()
print(f'Total courses in DB: {total}')

db.close()
