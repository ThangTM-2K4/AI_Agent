IF DB_ID('StudentAnalytics') IS NULL
BEGIN
    CREATE DATABASE StudentAnalytics;
END
GO

USE StudentAnalytics;
GO

IF OBJECT_ID('dbo.learning_activities', 'U') IS NOT NULL DROP TABLE dbo.learning_activities;
IF OBJECT_ID('dbo.course_results', 'U') IS NOT NULL DROP TABLE dbo.course_results;
IF OBJECT_ID('dbo.students', 'U') IS NOT NULL DROP TABLE dbo.students;
GO

CREATE TABLE dbo.students (
    id INT IDENTITY(1,1) PRIMARY KEY,
    student_code NVARCHAR(20) NOT NULL UNIQUE,
    full_name NVARCHAR(255) NOT NULL,
    class_name NVARCHAR(50) NULL
);

CREATE TABLE dbo.course_results (
    id INT IDENTITY(1,1) PRIMARY KEY,
    student_id INT NOT NULL,
    semester NVARCHAR(20) NOT NULL,
    course_code NVARCHAR(20) NOT NULL,
    course_name NVARCHAR(255) NOT NULL,
    credits INT NOT NULL,
    score FLOAT NOT NULL,
    CONSTRAINT FK_course_results_students FOREIGN KEY (student_id) REFERENCES dbo.students(id)
);

CREATE TABLE dbo.learning_activities (
    id INT IDENTITY(1,1) PRIMARY KEY,
    student_id INT NOT NULL,
    event_date DATE NOT NULL,
    metric_name NVARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    CONSTRAINT FK_learning_activities_students FOREIGN KEY (student_id) REFERENCES dbo.students(id)
);
GO

INSERT INTO dbo.students (student_code, full_name, class_name)
VALUES
('SV2026001', N'Nguyen Van An', 'CNTT-K18A'),
('SV2026002', N'Tran Thi Binh', 'CNTT-K18B');

INSERT INTO dbo.course_results (student_id, semester, course_code, course_name, credits, score)
VALUES
(1, '2025-1', 'MTH101', N'Giai tich 1', 3, 7.2),
(1, '2025-1', 'CSE101', N'Nhap mon lap trinh', 3, 8.1),
(1, '2025-2', 'CSE201', N'Cau truc du lieu', 3, 8.4),
(1, '2025-2', 'ENG201', N'Tieng Anh hoc thuat', 2, 7.5),
(2, '2025-1', 'MTH101', N'Giai tich 1', 3, 4.8),
(2, '2025-1', 'CSE101', N'Nhap mon lap trinh', 3, 5.6),
(2, '2025-2', 'CSE201', N'Cau truc du lieu', 3, 4.6),
(2, '2025-2', 'ENG201', N'Tieng Anh hoc thuat', 2, 5.1);

INSERT INTO dbo.learning_activities (student_id, event_date, metric_name, metric_value)
VALUES
(1, '2026-03-05', 'study_hours_week', 12),
(1, '2026-03-05', 'attendance_rate', 93),
(2, '2026-03-05', 'study_hours_week', 4),
(2, '2026-03-05', 'attendance_rate', 67);
GO
