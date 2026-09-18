# Data Dictionary

## Core Tables

| Table | Grain | Description |
| --- | --- | --- |
| `departments` | One row per academic department | Department code, name, and college. |
| `instructors` | One row per instructor | Instructor names and home department. |
| `courses` | One row per catalog course | Course metadata, department ownership, and credits. |
| `terms` | One row per academic term | Academic term labels and date ranges. |
| `sections` | One row per offered course section | Section capacity, instructor, course, and term. |
| `enrollments` | One row per student-section enrollment | Enrollment status and enrollment date. |
| `grades` | One row per graded enrollment | Letter and numeric grade outcome. |

## Reporting Metrics

| Metric | Definition |
| --- | --- |
| `enrolled_students` | Count of enrollments with `completed` or `failed` status. |
| `withdrawals` | Count of enrollments with `withdrawn` status. |
| `pass_rate_pct` | Passed students divided by graded enrollments. A, B, C, and D count as passing. |
| `capacity_utilization_pct` | Active enrollments divided by section capacity. |
| `average_grade` | Mean numeric grade for graded enrollments. |
| `sections_offered` | Distinct section count by department and term. |
