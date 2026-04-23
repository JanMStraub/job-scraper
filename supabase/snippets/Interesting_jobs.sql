SELECT job_title, level, description, source_url, resume_score, notes, is_interested
FROM jobs
WHERE resume_score >= 70
  AND is_active IS true
  AND job_state = 'new'
  AND is_interested IS NOT false
ORDER BY resume_score DESC
;