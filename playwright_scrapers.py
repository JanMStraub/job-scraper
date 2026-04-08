import time
import random
import logging
from urllib.parse import quote
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import config
from scraper import convert_html_to_markdown
import supabase_utils

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def setup_browser(p):
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-http2", "--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        user_agent=USER_AGENT,
        viewport={'width': 1280, 'height': 800},
        ignore_https_errors=True
    )
    return browser, context

def _human_delay(min_s=2, max_s=5):
    time.sleep(random.uniform(min_s, max_s))

# --- ARBEITSAGENTUR ---
def process_arbeitsagentur_query(query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting Arbeitsagentur Scraping for '{query}' ---")
    jobs = []
    
    with sync_playwright() as p:
        browser, context = setup_browser(p)
        page = context.new_page()
        
        try:
            url = f"https://www.arbeitsagentur.de/jobsuche/suche?angebotsart=1&was={quote(query)}&wo={quote(config.GERMANY_LOCATION)}"
            page.goto(url, wait_until="networkidle", timeout=30000)
            _human_delay()
            
            # Extract basic info
            job_cards = page.locator("a[href*='/jobsuche/jobdetail/']").all()
            links = []
            for card in job_cards:
                href = card.get_attribute("href")
                if href and '/jobsuche/jobdetail/' in href:
                    job_id = href.split('/')[-1]
                    url_out = href if href.startswith('http') else (f"https://www.arbeitsagentur.de{href}" if href.startswith('/') else f"https://www.arbeitsagentur.de/{href}")
                    links.append({"job_id": job_id, "url": url_out})
            
            links = links[:limit]
            
            # Simple deduplication placeholder. Ideally filter via supabase here:
            existing_ids, _ = supabase_utils.get_existing_jobs_from_supabase()
            new_links = [l for l in links if l["job_id"] not in existing_ids]
            
            for lnk in new_links:
                try:
                    page.goto(lnk["url"], wait_until="domcontentloaded")
                    _human_delay(1, 3)
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    title_elem = soup.find("h1")
                    title = title_elem.text.strip() if title_elem else "Unknown Title"
                    
                    company = None
                    # Arbeitsagentur layout changes, try generic matching
                    for div in soup.find_all("div"):
                        if "Arbeitgeber" in div.text:
                            ps = div.find_all("p")
                            if ps:
                                company = ps[0].text.strip()
                                break
                                
                    desc_div = soup.find("div", {"id": "detail-aufgabenplan"}) or soup.find("div", class_="ba-jobdetail-description")
                    desc_html = str(desc_div) if desc_div else html
                    
                    jobs.append({
                        "job_id": lnk["job_id"],
                        "company": company or "Unknown",
                        "job_title": title,
                        "location": config.GERMANY_LOCATION,
                        "level": "Not applicable",
                        "provider": "arbeitsagentur",
                        "description": convert_html_to_markdown(desc_html),
                        "posted_at": None
                    })
                except Exception as e:
                    logger.error(f"Error parsing Arbeitsagentur job {lnk['job_id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error hitting Arbeitsagentur: {e}")
        finally:
            browser.close()
    
    return jobs

# --- INDEED ---
def process_indeed_query(query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting Indeed Scraping for '{query}' ---")
    jobs = []
    
    with sync_playwright() as p:
        browser, context = setup_browser(p)
        page = context.new_page()
        
        try:
            url = f"https://de.indeed.com/jobs?q={quote(query)}&l={quote(config.GERMANY_LOCATION)}"
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
            _human_delay(3, 6)
            
            # Deal with cookie banner if needed
            try:
                page.click("button#onetrust-accept-btn-handler", timeout=3000)
                _human_delay(1, 2)
            except:
                pass
            
            cards = page.locator("a[data-jk]").all()
            job_ids = []
            for c in cards:
                jk = c.get_attribute("data-jk")
                if jk and jk not in job_ids:
                    job_ids.append(jk)
            
            job_ids = job_ids[:limit]
            
            existing_ids, _ = supabase_utils.get_existing_jobs_from_supabase()
            new_ids = [jid for jid in job_ids if jid not in existing_ids]
            
            for jid in new_ids:
                try:
                    detail_url = f"https://de.indeed.com/viewjob?jk={jid}"
                    page.goto(detail_url, wait_until="domcontentloaded")
                    _human_delay(2, 5)
                    
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    title_elem = soup.find("h1")
                    title = title_elem.text.strip() if title_elem else "Unknown"
                    
                    company_elem = soup.find("div", {"data-company-name": "true"}) or soup.find("span", {"data-testid": "inlineHeader-companyName"})
                    company = company_elem.text.strip() if company_elem else "Unknown"
                    
                    desc_elem = soup.find("div", {"id": "jobDescriptionText"})
                    desc_html = str(desc_elem) if desc_elem else "No description found"
                    
                    jobs.append({
                        "job_id": jid,
                        "company": company,
                        "job_title": title,
                        "location": config.GERMANY_LOCATION,
                        "level": "Not applicable",
                        "provider": "indeed",
                        "description": convert_html_to_markdown(desc_html),
                        "posted_at": None
                    })
                except Exception as e:
                    logger.error(f"Error parsing Indeed job {jid}: {e}")
                    
        except Exception as e:
            logger.error(f"Error hitting Indeed: {e}")
        finally:
            browser.close()
            
    return jobs

# --- STEPSTONE ---
def process_stepstone_query(query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting StepStone Scraping for '{query}' ---")
    jobs = []
    
    with sync_playwright() as p:
        browser, context = setup_browser(p)
        page = context.new_page()
        
        try:
            url = f"https://www.stepstone.de/jobs/{quote(query)}/in-{quote(config.GERMANY_LOCATION)}"
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
            _human_delay(3, 6)
            
            try:
                page.click("button#ccmgt_explicit_accept", timeout=3000)
                _human_delay(1, 2)
            except:
                pass
            
            article_links = page.locator("article a[href*='/stellenangebote-']").all()
            links = []
            for a in article_links:
                href = a.get_attribute("href")
                if href and href not in [l['url'] for l in links]:
                    # Generate a loose ID
                    job_id = href.split('-')[-1].replace('.html', '').split('?')[0]
                    links.append({"job_id": f"stepstone_{job_id}", "url": f"https://www.stepstone.de{href}"})
            
            links = links[:limit]
            
            existing_ids, _ = supabase_utils.get_existing_jobs_from_supabase()
            new_links = [l for l in links if l["job_id"] not in existing_ids]
            
            for lnk in new_links:
                try:
                    page.goto(lnk["url"], wait_until="domcontentloaded")
                    _human_delay(2, 5)
                    
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    title_elem = soup.find("h1")
                    title = title_elem.text.strip() if title_elem else "Unknown"
                    
                    company = "Unknown"
                    # Try to find company by looking at typical stepstone elements
                    company_link = soup.find("a", {"data-genesis-element": "company-link"})
                    if company_link:
                        company = company_link.text.strip()
                        
                    desc_html = html
                    # Generic fallback
                    jobs.append({
                        "job_id": lnk["job_id"],
                        "company": company,
                        "job_title": title,
                        "location": config.GERMANY_LOCATION,
                        "level": "Not applicable",
                        "provider": "stepstone",
                        "description": convert_html_to_markdown(desc_html)[:5000], # truncation for safety
                        "posted_at": None
                    })
                except Exception as e:
                    logger.error(f"Error parsing StepStone job {lnk['job_id']}: {e}")
        except Exception as e:
            logger.error(f"Error hitting StepStone: {e}")
        finally:
            browser.close()
            
    return jobs

# --- MEINESTADT ---
def process_meinestadt_query(query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting Meinestadt Scraping for '{query}' ---")
    jobs = []
    
    with sync_playwright() as p:
        browser, context = setup_browser(p)
        page = context.new_page()
        
        try:
            url = f"https://jobs.meinestadt.de/deutschland/suche?words={quote(query)}"
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            _human_delay(2, 4)
            
            cards = page.locator("a[href*='/stellenangebote/']").all()
            links = []
            for c in cards:
                href = c.get_attribute("href")
                if href and len(href) > 25: # filter out basic category links
                    job_id = href.split('/')[-1]
                    links.append({"job_id": f"meinestadt_{job_id}", "url": f"https://jobs.meinestadt.de{href}"})
            
            links = links[:limit]
            
            existing_ids, _ = supabase_utils.get_existing_jobs_from_supabase()
            new_links = [l for l in links if l["job_id"] not in existing_ids]
            
            for lnk in new_links:
                try:
                    page.goto(lnk["url"], wait_until="domcontentloaded")
                    _human_delay(1, 3)
                    
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    title_elem = soup.find("h1")
                    title = title_elem.text.strip() if title_elem else "Unknown"
                    
                    company = "Unknown"
                    # company logic
                    
                    desc_html = html
                    jobs.append({
                        "job_id": lnk["job_id"],
                        "company": company,
                        "job_title": title,
                        "location": config.GERMANY_LOCATION,
                        "level": "Not applicable",
                        "provider": "meinestadt",
                        "description": convert_html_to_markdown(desc_html)[:5000],
                        "posted_at": None
                    })
                except Exception as e:
                    logger.error(f"Error parsing Meinestadt job {lnk['job_id']}: {e}")
        except Exception as e:
            logger.error(f"Error hitting Meinestadt: {e}")
        finally:
            browser.close()
            
    return jobs

# --- JOOBLE ---
def process_jooble_query(query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting Jooble Scraping for '{query}' ---")
    jobs = []
    
    with sync_playwright() as p:
        browser, context = setup_browser(p)
        page = context.new_page()
        
        try:
            url = f"https://de.jooble.org/Stellenangebote-{quote(query)}/{quote(config.GERMANY_LOCATION)}"
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
            _human_delay(2, 5)
            
            cards = page.locator("article").all()
            job_ids = []
            for c in cards:
                jid = c.get_attribute("data-id")
                if jid and jid not in job_ids:
                    job_ids.append(jid)
            
            job_ids = job_ids[:limit]
            
            existing_ids, _ = supabase_utils.get_existing_jobs_from_supabase()
            new_ids = [jid for jid in job_ids if jid not in existing_ids]
            
            for jid in new_ids:
                try:
                    detail_url = f"https://de.jooble.org/desc/{jid}"
                    page.goto(detail_url, wait_until="domcontentloaded")
                    _human_delay(2, 4)
                    
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    title_elem = soup.find("h1")
                    title = title_elem.text.strip() if title_elem else "Unknown"
                    
                    desc_html = html
                    jobs.append({
                        "job_id": jid,
                        "company": "Unknown",
                        "job_title": title,
                        "location": config.GERMANY_LOCATION,
                        "level": "Not applicable",
                        "provider": "jooble",
                        "description": convert_html_to_markdown(desc_html)[:5000],
                        "posted_at": None
                    })
                except Exception as e:
                    logger.error(f"Error parsing Jooble job {jid}: {e}")
        except Exception as e:
            logger.error(f"Error hitting Jooble: {e}")
        finally:
            browser.close()
            
    return jobs
