CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS staging.departments (
    department_id INTEGER PRIMARY KEY,
    department_code TEXT NOT NULL UNIQUE,
    department_name TEXT NOT NULL,
    college TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS staging.instructors (
    instructor_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES staging.departments(department_id)
);

CREATE TABLE IF NOT EXISTS staging.courses (
    course_id INTEGER PRIMARY KEY,
    course_code TEXT NOT NULL UNIQUE,
    course_title TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES staging.departments(department_id),
    credits INTEGER NOT NULL CHECK (credits > 0)
);

CREATE TABLE IF NOT EXISTS staging.terms (
    term_id INTEGER PRIMARY KEY,
    term_code TEXT NOT NULL UNIQUE,
    term_name TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    CHECK (end_date > start_date)
);

CREATE TABLE IF NOT EXISTS staging.sections (
    section_id INTEGER PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES staging.courses(course_id),
    term_id INTEGER NOT NULL REFERENCES staging.terms(term_id),
    instructor_id INTEGER NOT NULL REFERENCES staging.instructors(instructor_id),
    section_number TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    UNIQUE (course_id, term_id, section_number)
);

CREATE TABLE IF NOT EXISTS staging.enrollments (
    enrollment_id INTEGER PRIMARY KEY,
    student_id TEXT NOT NULL,
    section_id INTEGER NOT NULL REFERENCES staging.sections(section_id),
    enrollment_status TEXT NOT NULL CHECK (enrollment_status IN ('completed', 'withdrawn', 'failed')),
    enrolled_date DATE NOT NULL,
    UNIQUE (student_id, section_id)
);

CREATE TABLE IF NOT EXISTS staging.grades (
    enrollment_id INTEGER PRIMARY KEY REFERENCES staging.enrollments(enrollment_id),
    letter_grade TEXT NOT NULL CHECK (letter_grade IN ('A', 'B', 'C', 'D', 'F')),
    numeric_grade NUMERIC(5, 2) NOT NULL CHECK (numeric_grade BETWEEN 0 AND 100)
);

CREATE OR REPLACE VIEW analytics.v_enrollment_outcomes AS
SELECT
    e.enrollment_id,
    e.student_id,
    e.enrollment_status,
    e.enrolled_date,
    s.section_id,
    s.section_number,
    s.capacity,
    t.term_id,
    t.term_name,
    c.course_id,
    c.course_code,
    c.course_title,
    d.department_id,
    d.department_code,
    d.department_name,
    d.college,
    g.letter_grade,
    g.numeric_grade,
    CASE WHEN e.enrollment_status IN ('completed', 'failed') THEN 1 ELSE 0 END AS is_enrolled,
    CASE WHEN g.letter_grade IN ('A', 'B', 'C', 'D') THEN 1 ELSE 0 END AS is_passed,
    CASE WHEN g.letter_grade = 'F' THEN 1 ELSE 0 END AS is_failed,
    CASE WHEN e.enrollment_status = 'withdrawn' THEN 1 ELSE 0 END AS is_withdrawn
FROM staging.enrollments e
JOIN staging.sections s ON e.section_id = s.section_id
JOIN staging.courses c ON s.course_id = c.course_id
JOIN staging.departments d ON c.department_id = d.department_id
JOIN staging.terms t ON s.term_id = t.term_id
LEFT JOIN staging.grades g ON e.enrollment_id = g.enrollment_id;

CREATE OR REPLACE VIEW analytics.v_enrollment_trends AS
SELECT
    term_id,
    term_name,
    department_code,
    SUM(is_enrolled) AS enrolled_students,
    SUM(is_withdrawn) AS withdrawals,
    ROUND(AVG(numeric_grade), 2) AS average_grade
FROM analytics.v_enrollment_outcomes
GROUP BY term_id, term_name, department_code;

CREATE OR REPLACE VIEW analytics.v_capacity_utilization AS
SELECT
    term_id,
    term_name,
    department_code,
    course_code,
    course_title,
    section_id,
    SUM(is_enrolled) AS enrolled_students,
    MAX(capacity) AS capacity,
    ROUND(SUM(is_enrolled)::NUMERIC / NULLIF(MAX(capacity), 0) * 100, 2) AS capacity_utilization_pct
FROM analytics.v_enrollment_outcomes
GROUP BY term_id, term_name, department_code, course_code, course_title, section_id;

CREATE OR REPLACE VIEW analytics.v_pass_rates AS
SELECT
    term_id,
    term_name,
    department_code,
    course_code,
    COUNT(*) FILTER (WHERE enrollment_status IN ('completed', 'failed')) AS graded_enrollments,
    SUM(is_passed) AS passed_students,
    SUM(is_failed) AS failed_students,
    ROUND(
        SUM(is_passed)::NUMERIC
        / NULLIF(COUNT(*) FILTER (WHERE enrollment_status IN ('completed', 'failed')), 0)
        * 100,
        2
    ) AS pass_rate_pct,
    ROUND(AVG(numeric_grade), 2) AS average_grade
FROM analytics.v_enrollment_outcomes
WHERE enrollment_status IN ('completed', 'failed')
GROUP BY term_id, term_name, department_code, course_code;

CREATE OR REPLACE VIEW analytics.v_department_performance AS
WITH outcome_metrics AS (
    SELECT
        term_id,
        term_name,
        department_code,
        department_name,
        college,
        COUNT(DISTINCT section_id) AS sections_offered,
        SUM(is_enrolled) AS active_enrollments,
        SUM(is_withdrawn) AS withdrawals,
        SUM(is_passed) AS passed_students,
        ROUND(SUM(is_passed)::NUMERIC / NULLIF(SUM(is_enrolled), 0) * 100, 2) AS pass_rate_pct,
        ROUND(AVG(numeric_grade), 2) AS average_grade
    FROM analytics.v_enrollment_outcomes
    GROUP BY term_id, term_name, department_code, department_name, college
),
section_capacity AS (
    SELECT
        t.term_id,
        d.department_code,
        SUM(s.capacity) AS total_capacity
    FROM staging.sections s
    JOIN staging.courses c ON s.course_id = c.course_id
    JOIN staging.departments d ON c.department_id = d.department_id
    JOIN staging.terms t ON s.term_id = t.term_id
    GROUP BY t.term_id, d.department_code
)
SELECT
    o.term_id,
    o.term_name,
    o.department_code,
    o.department_name,
    o.college,
    o.sections_offered,
    o.active_enrollments,
    o.withdrawals,
    o.passed_students,
    o.pass_rate_pct,
    o.average_grade,
    ROUND(o.active_enrollments::NUMERIC / NULLIF(c.total_capacity, 0) * 100, 2) AS capacity_utilization_pct
FROM outcome_metrics o
JOIN section_capacity c
    ON o.term_id = c.term_id
    AND o.department_code = c.department_code;
