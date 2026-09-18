SELECT
    term_name,
    college,
    department_code,
    department_name,
    sections_offered,
    active_enrollments,
    withdrawals,
    pass_rate_pct,
    average_grade,
    capacity_utilization_pct
FROM analytics.v_department_performance
ORDER BY term_id, active_enrollments DESC;
