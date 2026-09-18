SELECT
    term_name,
    department_code,
    course_code,
    course_title,
    enrolled_students,
    capacity,
    capacity_utilization_pct
FROM analytics.v_capacity_utilization
ORDER BY term_id, capacity_utilization_pct DESC;
