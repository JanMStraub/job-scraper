UPDATE jobs 
SET resume_score = NULL, 
    notes = NULL;

ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS source_url text;
