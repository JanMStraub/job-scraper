# Job Scraper & Application Assistant

This project is a comprehensive suite of tools designed to automate and enhance the job searching process, primarily focusing on LinkedIn and German job portals. It scrapes job postings, parses resumes, scores job suitability against a candidate's resume, manages job application statuses, and can even generate custom PDF resumes. The system is designed to run locally, leveraging local AI models (such as LM Studio/Ollama) for advanced text processing and a local instance of Supabase for data storage.

## Features

- **Job Scraping**: Automatically scrapes job postings. ([scraper.py](scraper.py))
- **Resume Parsing**:
  - Extracts text from PDF resumes using `pdfplumber`. ([resume_parser.py](resume_parser.py))
  - Utilizes Google Gemini AI to parse resume text into structured data ([parse_resume_with_ai.py](parse_resume_with_ai.py))
- **Job Scoring**: Scores job descriptions against a parsed resume using AI to determine suitability. ([score_jobs.py](score_jobs.py))
- **Universal LLM Support**: Supports 400+ model providers (Gemini, OpenAI, Anthropic, Ollama, Groq, etc.) via a unified abstraction layer. ([llm_client.py](llm_client.py))
- **Job Management**:
  - Tracks the status of job applications.
  - Marks old or inactive jobs as expired.
  - Periodically checks if active jobs are still available.
    ([job_manager.py](job_manager.py))
- **Data Storage**: Uses Supabase to store job data, resume details, and application statuses. (Utility functions in [supabase_utils.py](supabase_utils.py))
- **Custom PDF Resume Generation**: Generates ATS-friendly PDF resumes from structured resume data. ([pdf_generator.py](pdf_generator.py))
- **AI-Powered Text Processing**: Leverages any configured LLM for tasks like resume parsing and job description formatting.
- **Quota Management**: Built-in rate limiting, exponential backoff, and daily budget tracking for LLM API calls. Features dynamic model rotation (e.g., automatically switching between Gemini models) to bypass rate limitations.
- **Local-First Architecture**: Completely removes reliance on external pipelines or GitHub actions to protect your data natively on your machine, leveraging local endpoints.

## Tech Stack

- **Programming Language**: Python 3.11.9
- **Web Scraping/HTTP**:
  - `requests`
  - `httpx`
  - `BeautifulSoup4` (for HTML parsing)
  - `Playwright` (for browser automation)
- **PDF Processing**:
  - `pdfplumber` (for text extraction)
  - `ReportLab` (for PDF generation)
- **AI/LLM**: `litellm` (Universal proxy supporting Gemini, OpenAI, Claude, etc.), `google-genai`
- **Database**: Supabase (`supabase`)
- **Data Validation**: `Pydantic`
- **Environment Management**: `python-dotenv`
- **Text Conversion**: `html2text`
- **CI/CD**: GitHub Actions

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
    - Set up the necessary tables and buckets from the output.

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

    - Run the scripts individually or set up a local cron job to execute them:
      ```bash
      python scraper.py
      python score_jobs.py
      python custom_resume_generator.py
      ```

## Usage

After the initial setup and the parser has successfully run, the system will operate when the crawler is invoked via `python scraper.py`.

You can interact with the data directly through your Supabase dashboard to view scraped jobs, your parsed resume, and job scores.

### Web Interface for Viewing Data

A Next.js web application is available to view and manage the scraped jobs, your resume details, and job scores from the database.

- **Repository:** [jobs-scrapper-web](https://github.com/anandanair/jobs-scraper-web)
### Running Locally

All scripts execute locally to avoid tracking quotas across networks:

1. Scraping and saving jobs: `python scraper.py`
2. Evaluating AI job scores: `python score_jobs.py`
3. Managing expired DB states: `python job_manager.py`



## Project Structure

```
.
├── .gitignore                  # Specifies intentionally untracked files that Git should ignore
├── README.md                   # This file
├── config.py                   # Configuration settings (API keys, search parameters)
├── custom_resume_generator.py  # Script to generate customized resumes (if applicable)
├── job_manager.py              # Manages job statuses
├── llm_client.py               # Universal LLM abstraction (LiteLLM) with rate limiting
├── models.py                   # Pydantic models for data validation
├── pdf_generator.py            # Generates PDF resumes
├── requirements.txt            # Python dependencies
├── resume_parser.py            # Parses resume PDF from Supabase Storage and saves to DB
├── score_jobs.py               # Scores job suitability against resumes
├── scraper.py                  # Core scraping logic for LinkedIn and CareersFuture
├── supabase_setup/             # SQL scripts for Supabase database initialization
│   └── init.sql
├── supabase_utils.py           # Utility functions for interacting with Supabase
└── user_agents.py              # List of user-agents for web scraping
```

## Contributing

Contributions are welcome! If you'd like to contribute, please follow these steps:

1.  **Fork the Repository:** Create your own fork of the project on GitHub.
2.  **Create a Branch:** Create a new branch in your fork for your feature or bug fix (e.g., `git checkout -b feature/your-awesome-feature` or `git checkout -b fix/issue-description`).
3.  **Make Changes:** Implement your changes in your branch.
4.  **Test Your Changes:** Ensure your changes work as expected and do not break existing functionality.
5.  **Commit Your Changes:** Commit your changes with clear and descriptive commit messages (e.g., `git commit -m 'feat: Add awesome new feature'`).
6.  **Push to Your Fork:** Push your changes to your forked repository (`git push origin feature/your-awesome-feature`).
7.  **Open a Pull Request:** Go to the original repository and open a Pull Request from your forked branch to the main branch of the original repository. Provide a clear description of your changes in the Pull Request.

Please ensure your code adheres to the existing style and that any new dependencies are added to `requirements.txt`.

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

This project is for educational and personal use only. Scraping websites like LinkedIn may be against their Terms of Service. Use this tool responsibly and at your own risk. The developers of this project are not responsible for any misuse or any action taken against your account by LinkedIn or other platforms.

## Contact

If you have any questions, suggestions, or issues, please open an issue on the GitHub repository.
