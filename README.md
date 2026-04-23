# Job Scraper & Application Assistant

This project is a comprehensive suite of tools designed to automate and enhance the job searching process, primarily focusing on LinkedIn, Xing, and various German job portals. It scrapes job postings, parses resumes, scores job suitability against a candidate's resume, manages job application statuses, and can even generate custom PDF resumes and cover letters. The system is designed to run locally, leveraging local AI models (such as LM Studio/Ollama) for advanced text processing and a local instance of Supabase for data storage.

## New Features (Recent Updates)

- **Streamlit Dashboard**: A new interactive local UI to view high-relevance jobs (score >= 70), reject unsuitable matches, and trigger background generation of tailored application documents. ([app.py](app.py))
- **Pipeline Automation**: A unified `run_pipeline.sh` script to execute the entire workflow (scraping, cleaning, scoring, and dashboard) in one go.
- **Expanded Job Portals**: Support for **Xing**, **Workwise**, and **Museumsbund.de**, in addition to LinkedIn and CareersFuture.
- **AI Cover Letter Generation**: Automated generation of professional "Anschreiben" in German or English, tailored specifically to the job description and your resume. ([anschreiben_generator.py](anschreiben_generator.py))
- **Enhanced Scraping Robustness**: 
  - Integrated **Proxy Support** for Playwright.
  - Configurable **Search Radius** for all portals.
  - Automated job activity checks to mark expired listings.
- **Local LLM Optimization**: Implemented JSON cleaning, whitespace normalization, and sequential processing to ensure stability when using local models like Llama 3 or Mistral.

## Features

- **Job Scraping**: Automatically scrapes job postings from LinkedIn, Xing, CareersFuture, Workwise, and Museumsbund. ([scraper.py](scraper.py), [playwright_scrapers.py](playwright_scrapers.py))
- **Resume Parsing**:
  - Extracts text from PDF resumes using `pdfplumber`. ([resume_parser.py](resume_parser.py))
  - Utilizes AI to parse resume text into structured data.
- **Job Scoring**: Scores job descriptions against a parsed resume using AI to determine suitability. ([score_jobs.py](score_jobs.py))
- **Universal LLM Support**: Supports 400+ model providers (Gemini, OpenAI, Anthropic, Ollama, Groq, etc.) via a unified abstraction layer. ([llm_client.py](llm_client.py))
- **Job Management**:
  - Tracks the status of job applications.
  - Marks old or inactive jobs as expired.
  - Periodically checks if active jobs are still available.
    ([job_manager.py](job_manager.py))
- **Data Storage**: Uses Supabase to store job data, resume details, and application statuses. (Utility functions in [supabase_utils.py](supabase_utils.py))
- **Custom PDF Resume & Cover Letter Generation**: Generates ATS-friendly PDF resumes and AI-tailored cover letters. ([pdf_generator.py](pdf_generator.py), [anschreiben_generator.py](anschreiben_generator.py))
- **Quota Management**: Built-in rate limiting, exponential backoff, and daily budget tracking for LLM API calls.
- **Local-First Architecture**: Completely removes reliance on external pipelines, protecting your data natively on your machine.

## Tech Stack

- **Programming Language**: Python 3.11.9
- **Web Scraping/HTTP**: `requests`, `httpx`, `BeautifulSoup4`, `Playwright` (with proxy support)
- **UI Framework**: `Streamlit` (for the dashboard)
- **PDF Processing**: `pdfplumber`, `ReportLab`
- **AI/LLM**: `litellm` (Universal proxy), `google-genai`
- **Database**: Supabase (`supabase`)
- **Data Validation**: `Pydantic`
- **Environment Management**: `python-dotenv`

## Setup and Installation

This project is designed to run locally on your machine. Follow these steps to set it up:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/job-scraper.git
    cd job-scraper
    ```

2.  **Environment Setup:**
    - Python 3.11+ is required.
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    playwright install
    ```

3.  **Create a Local Supabase Instance:**
    - Install the Supabase CLI: `brew install supabase/tap/supabase` (on macOS).
    - Run `supabase start` in your project folder to boot the local database.
    - Set up the necessary tables and buckets from the output or use scripts in `supabase_setup/`.

4.  **Local AI Setup (LM Studio / Ollama):**
    - You can run your LLMs locally to process resumes and match jobs.
    - Start LM Studio and boot up the local server (usually `http://localhost:1234/v1`).
    - Create a `.env` file in the root directory:
      ```env
      LLM_API_BASE="http://localhost:1234/v1"
      LLM_API_KEY="lm-studio"
      SUPABASE_URL="http://127.0.0.1:54321"
      SUPABASE_SERVICE_ROLE_KEY="YOUR_LOCAL_SERVICE_ROLE_KEY"
      ```

5.  **Parse Your Resume:**
    - Place your `resume.pdf` file in the appropriate Supabase local storage bucket or the project directory.
    - Run the parser script locally: 
      ```bash
      python resume_parser.py
      ```

6.  **Configure Job Search Parameters (Edit `config.py`):**
    - Navigate to the `config.py` file to set your portals and target titles:

      ```python
      # --- LinkedIn Search Configuration ---
      LINKEDIN_SEARCH_QUERIES = ["maths lecturer", "statistics lecturer"] # Your keywords
      LINKEDIN_LOCATION = "Singapore" # Target location
      LINKEDIN_GEO_ID = 102454443 # Geo ID (Singapore: 102454443, Dubai: 100205264)
      LINKEDIN_JOB_TYPE = "F" # "F" for Full-time
      LINKEDIN_JOB_POSTING_DATE = "r86400" # "r86400" for past 24 hours

      # --- Careers Future Search Configuration ---
      CAREERS_FUTURE_SEARCH_QUERIES = ["IT Support", "Full Stack Web Developer"]
      CAREERS_FUTURE_SEARCH_CATEGORIES = ["Information Technology"]

      # --- LLM configuration ---
      # For a full list of 100+ supported providers and model naming schemes, see:
      # https://docs.litellm.ai/docs/providers

      LLM_MODEL = "gemini"            # Model to use
      LLM_MAX_RPM = 10                # Max requests per minute
      LLM_REQUEST_DELAY_SECONDS = 8   # Delay between calls

      # --- Processing Limits ---
      JOBS_TO_SCORE_PER_RUN = 1       # Scaled for free tier
      MAX_JOBS_PER_SEARCH = {
          "linkedin": 2,
          "careers_future": 10,
      }
      ```

## Usage

### The Easy Way: Integrated Pipeline
Run the entire automated workflow with a single command:
```bash
./run_pipeline.sh
```
This script will:
1. Scrape new jobs.
2. Clean up expired listings.
3. Score new jobs against your resume.
4. Launch the Streamlit dashboard.

### The Manual Way: Individual Components
All scripts execute locally to avoid tracking quotas across networks:
1. **Scraping and saving jobs**: `python scraper.py`
2. **Evaluating AI job scores**: `python score_jobs.py`
3. **Managing expired DB states**: `python job_manager.py`
4. **Dashboard**: `streamlit run app.py`

### Interactive Dashboard
The Streamlit dashboard (`app.py`) allows you to:
- Review jobs with high suitability scores (>= 70).
- Read full job descriptions.
- **Reject** jobs to remove them from your view.
- **Generate Anschreiben**: Triggers the AI to create a tailored cover letter and resume PDF for the specific job.

## Project Structure

```
.
├── app.py                      # Streamlit dashboard UI
├── run_pipeline.sh             # Master automation script
├── anschreiben_generator.py    # AI logic for tailored cover letters
├── scraper.py                  # Core scraping orchestrator
├── playwright_scrapers.py      # Detailed scraping logic (LinkedIn, Xing, etc.)
├── score_jobs.py               # AI scoring logic
├── job_manager.py              # Database maintenance and expiry checks
├── llm_client.py               # Universal LLM abstraction
├── pdf_generator.py            # PDF generation (Resume & Cover Letters)
├── resume_parser.py            # Converts PDF resume to structured DB data
├── supabase_utils.py           # Database interaction layer
├── config.py                   # Configuration (Queries, Radius, Models)
├── models.py                   # Data schemas (Pydantic)
└── requirements.txt            # Project dependencies
```

## Contributing

Contributions are welcome! If you'd like to contribute, please follow these steps:

1.  **Fork the Repository:** Create your own fork of the project on GitHub.
2.  **Create a Branch:** Create a new branch in your fork for your feature or bug fix (e.g., `git checkout -b feature/your-awesome-feature`).
3.  **Make Changes:** Implement your changes in your branch.
4.  **Test Your Changes:** Ensure your changes work as expected and do not break existing functionality.
5.  **Commit Your Changes:** Commit your changes with clear and descriptive commit messages.
6.  **Push to Your Fork:** Push your changes to your forked repository.
7.  **Open a Pull Request:** Go to the original repository and open a Pull Request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Acknowledgements

- This project utilizes [LiteLLM](https://docs.litellm.ai/) as a universal proxy to support 400+ LLM providers.
- Originally built with the powerful [Google Gemini API](https://ai.google.dev/models/gemini) for AI-driven text processing.
- Data storage is managed with [Supabase](https://supabase.com/), an excellent open-source Firebase alternative.
- Web scraping capabilities are enhanced by [Playwright](https://playwright.dev/) and [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/).
- PDF generation is handled by [ReportLab](https://www.reportlab.com/).
- PDF text extraction is performed using [pdfplumber](https://github.com/jsvine/pdfplumber).

## Disclaimer

This project is for educational and personal use only. Scraping websites like LinkedIn or Xing may be against their Terms of Service. Use this tool responsibly and at your own risk. The developers of this project are not responsible for any misuse or any action taken against your account by LinkedIn or other platforms.

## Contact

If you have any questions, suggestions, or issues, please open an issue on the GitHub repository.
