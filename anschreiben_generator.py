"""
anschreiben_generator.py

Generates a structured cover letter (Anschreiben) using the LLM, tailored to
the job description in either German or English.
"""
import logging
import json
from typing import Dict, Any

import config
from llm_client import primary_client
from models import Resume, Anschreiben

logger = logging.getLogger(__name__)


def _build_prompt(resume: Resume, job_details: Dict[str, Any], language: str) -> str:
    """Build the cover letter generation prompt."""

    is_german = language.lower() == "german"

    # Language-specific instructions
    if is_german:
        lang_instruction = (
            "Schreibe das Anschreiben auf Deutsch im professionellen DIN-5008-Stil. "
            "Verwende 'Sie' (formelle Anrede). "
            "Betreff-Zeile: kurz und prägnant (z.B. 'Bewerbung als Python-Entwickler'). "
            "Anrede: 'Sehr geehrte Damen und Herren,' (oder ggf. mit Name wenn angegeben). "
            "Schluss: 'Mit freundlichen Grüßen'."
        )
        opening_example = "Sehr geehrte Damen und Herren,"
        closing_example = "Mit freundlichen Grüßen"
    else:
        lang_instruction = (
            "Write the cover letter in professional British/American English. "
            "Subject line: short and descriptive (e.g. 'Application for Python Developer Position'). "
            "Opening: 'Dear Hiring Team,' or 'Dear Sir or Madam,'. "
            "Closing: 'Sincerely' or 'Kind regards'."
        )
        opening_example = "Dear Hiring Team,"
        closing_example = "Sincerely"

    # Format resume highlights concisely
    skills = ", ".join(resume.skills[:10]) if resume.skills else "N/A"
    latest_exp = resume.experience[0] if resume.experience else None
    exp_text = (
        f"{latest_exp.job_title} at {latest_exp.company} ({latest_exp.start_date}–{latest_exp.end_date})"
        if latest_exp else "N/A"
    )

    return f"""
You are an expert career consultant writing a professional cover letter.

{lang_instruction}

--- APPLICANT INFORMATION ---
Name: {resume.name}
Location: {resume.location}
Email: {resume.email}
Summary: {resume.summary}
Key Skills: {skills}
Most Recent Role: {exp_text}

--- TARGET JOB ---
Company: {job_details.get('company', 'N/A')}
Job Title: {job_details.get('job_title', 'N/A')}
Job Description:
{job_details.get('description', 'N/A')[:2000]}

--- OUTPUT FORMAT ---
Return a valid JSON object with these exact keys:
{{
  "subject": "...",
  "opening": "{opening_example}",
  "body_paragraphs": [
    "First paragraph: why you are interested in this specific company and role.",
    "Second paragraph: your most relevant experience and skills for this role.",
    "Third paragraph: what you bring and a confident closing statement."
  ],
  "closing": "{closing_example}"
}}

Rules:
- body_paragraphs must be a JSON array of 3 strings
- Each paragraph should be 2-4 sentences
- Do NOT use placeholders like [Your Name] — use the actual applicant data
- Do NOT include any text outside the JSON object
"""


async def generate_anschreiben(
    resume: Resume,
    job_details: Dict[str, Any],
    language: str = "german"
) -> Anschreiben | None:
    """
    Generate a structured Anschreiben (cover letter) using the LLM.

    Args:
        resume:      The applicant's parsed resume.
        job_details: The target job dict from Supabase.
        language:    "german" or "english"

    Returns:
        An Anschreiben Pydantic model, or None on failure.
    """
    job_id = job_details.get("job_id", "unknown")
    logger.info(f"Generating Anschreiben for job_id={job_id} in language='{language}'")

    prompt = _build_prompt(resume, job_details, language)

    try:
        raw = await primary_client.agenerate_content(
            prompt=prompt,
            response_format=Anschreiben
        )
    except Exception as e:
        logger.error(f"LLM call failed for Anschreiben (job_id={job_id}): {e}")
        return None

    # Strip markdown fences if present
    import re
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)

    try:
        anschreiben = Anschreiben.model_validate_json(raw)
        logger.info(f"Successfully parsed Anschreiben for job_id={job_id}")
        return anschreiben
    except Exception as e:
        logger.warning(f"Pydantic parse failed for job_id={job_id}, trying manual JSON: {e}")
        try:
            data = json.loads(raw)
            return Anschreiben(**data)
        except Exception as e2:
            logger.error(f"All Anschreiben parsing failed for job_id={job_id}: {e2}\nRaw: {raw[:300]}")
            return None
