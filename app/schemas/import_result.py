from pydantic import BaseModel


class ImportResult(BaseModel):
    students_upserted: int
    course_results_imported: int
    learning_activities_imported: int
    message: str