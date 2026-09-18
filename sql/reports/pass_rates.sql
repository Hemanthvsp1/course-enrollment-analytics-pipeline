SELECT
    term_name,
    department_code,
    course_code,
    graded_enrollments,
    passed_students,
    failed_students,
    pass_rate_pct,
    average_grade
FROM analytics.v_pass_rates
ORDER BY term_id, pass_rate_pct DESC;
