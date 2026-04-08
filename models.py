from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date

class Education(BaseModel):
    degree: str = ""
    field_of_study: str = ""
    institution: str = ""
    start_year: str = ""
    end_year: str = ""

class Experience(BaseModel):
    job_title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""

class Project(BaseModel):
    name: str = ""
    description: str = ""
    technologies: List[str] = Field(default_factory=list)

class Certification(BaseModel):
    name: str = ""
    issuer: str = ""
    year: str = ""

class Links(BaseModel):
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""

class Resume(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    links: Links = Field(default_factory=Links)

# --- Pydantic models for LLM structured output ---
class SummaryOutput(BaseModel):
    summary: str

class SkillsOutput(BaseModel):
    skills: List[str]

class ExperienceListOutput(BaseModel):
    experience: List[Experience]

class SingleExperienceOutput(BaseModel):
    experience: Experience

class JobScoreOutput(BaseModel):
    thinking: str = Field(default="", description="Your internal step-by-step reasoning. Analyze the resume skills vs job requirements, identify matches and gaps, then decide on a score.")
    score: int = Field(ge=0, le=100, description="A score between 0 and 100")
    reason: str = Field(description="A highly concise explanation using short bullet points (max 3)")

class ProjectListOutput(BaseModel):
    projects: List[Project]

class SingleProjectOutput(BaseModel):
    project: Project

class ValidationResponse(BaseModel):
    is_valid: bool
    reason: str

class Anschreiben(BaseModel):
    """Structured cover letter content for PDF generation."""
    subject: str = Field(description="The subject line of the cover letter")
    opening: str = Field(description="The salutation line")
    body_paragraphs: List[str] = Field(description="List of body paragraphs (2-4 paragraphs)")
    closing: str = Field(description="The closing line before signature")

class Config:
    extra = 'allow'