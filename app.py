import streamlit as st
import pandas as pd
from supabase_utils import supabase
import subprocess
import os

st.set_page_config(page_title="Job Scraper Dashboard", layout="wide")

st.title("Job Scraper Dashboard")

# Initialize session state for generating jobs so they can be hidden/styled after clicking
if "generating_jobs" not in st.session_state:
    st.session_state.generating_jobs = set()

def fetch_jobs():
    response = supabase.table('jobs') \
        .select("job_id, job_title, company, level, description, source_url, resume_score, notes, is_interested") \
        .gte("resume_score", 70) \
        .eq("is_active", True) \
        .eq("job_state", "new") \
        .or_("is_interested.is.null,is_interested.eq.true") \
        .order("resume_score", desc=True) \
        .execute()
    return response.data

def reject_job(job_id):
    supabase.table("jobs").update({"job_state": "rejected", "is_interested": False}).eq("job_id", job_id).execute()

def mark_interested_and_generate(job_id):
    # Mark as interested in the database
    supabase.table("jobs").update({"is_interested": True}).eq("job_id", job_id).execute()
    st.session_state.generating_jobs.add(job_id)
    
    # Trigger the background pipeline
    # We will use the scraper virtual environment if it exists
    python_exec = "scraper/bin/python" if os.path.exists("scraper/bin/python") else "python"
    
    # Run custom_resume_generator.py in the background
    # This will process jobs marked as new, with resume_score >= 50, and customized_resume_id IS NULL
    # including the one we just verified is_interested=True
    subprocess.Popen([python_exec, "custom_resume_generator.py"])

jobs = fetch_jobs()

if not jobs:
    st.info("No top-scored new jobs available right now.")
else:
    # Filter out jobs that are currently being generated in this session
    display_jobs = [job for job in jobs if job['job_id'] not in st.session_state.generating_jobs]
    
    st.subheader(f"Found {len(display_jobs)} Top-Scored Jobs")
    
    for job in display_jobs:
        score = job.get("resume_score", 0)
        company = job.get("company", "Unknown")
        title = job.get("job_title", "Unknown")
        level = job.get("level", "N/A")
        
        with st.expander(f"[{score}] {title} @ {company}"):
            st.write(f"**Level:** {level}")
            url = job.get("source_url")
            if url:
                st.write(f"**Source URL:** [{url}]({url})")
            
            notes = job.get("notes")
            if notes:
                st.write(f"**Notes:** {notes}")
            
            col1, col2, col3 = st.columns([1, 2, 4])
            with col1:
                if st.button("Reject", key=f"reject_{job['job_id']}"):
                    reject_job(job['job_id'])
                    st.rerun()
            with col2:
                if st.button("Generate Anschreiben", key=f"generate_{job['job_id']}"):
                    mark_interested_and_generate(job['job_id'])
                    st.success("Background generation started! PDF will be available in Supabase shortly.")
                    st.rerun()
            
            st.markdown("### Description")
            st.markdown(job.get("description", "No description provided."))

if st.session_state.generating_jobs:
    st.sidebar.subheader("Currently Generating:")
    for job_id in st.session_state.generating_jobs:
        st.sidebar.text(f"Job ID: {job_id[:8]}...")
