SELECT
    term_name,
    department_code,
    enrolled_students,
    withdrawals,
    average_grade
FROM analytics.v_enrollment_trends
ORDER BY term_id, department_code;
