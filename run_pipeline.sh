#!/bin/bash
# Script to run the job scraper and scorer pipeline

# Change to the project directory
cd /Users/jan/Developer/job-scraper || exit 1

# Activate the scraper virtual environment
source scraper/bin/activate

# Run the scraper
echo "Starting scraper..."
python scraper.py
if [ $? -ne 0 ]; then
    echo "Scraper failed. Exiting."
    exit 1
fi

# Run the job manager (Cleanup & Activity Checks)
echo "Starting job manager..."
python job_manager.py
if [ $? -ne 0 ]; then
    echo "Job manager failed. Exiting."
    exit 1
fi

# Run the scorer
echo "Starting scorer..."
python score_jobs.py
if [ $? -ne 0 ]; then
    echo "Scorer failed. Exiting."
    exit 1
fi

echo "Pipeline completed successfully."

# Start the dashboard if it isn't already running
if ! pgrep -f "streamlit run app.py" > /dev/null; then
    echo "Starting Streamlit dashboard in the background..."
    nohup streamlit run app.py > streamlit.log 2>&1 &
else
    echo "Streamlit dashboard is already running."
fi
