import time
import random
import logging
import re
from urllib.parse import quote
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth
import config
from scraper import convert_html_to_markdown
import supabase_utils

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def setup_browser(p):
    launch_args = {
        "headless": True,
        "args": ["--disable-http2", "--disable-blink-features=AutomationControlled"]
    }
    
    if getattr(config, 'USE_PROXIES', False) and getattr(config, 'PROXY_LIST', []):
        proxy_server = random.choice(config.PROXY_LIST)
        launch_args["proxy"] = {"server": proxy_server}
        logger.info(f"Playwright using proxy: {proxy_server}")

    browser = p.chromium.launch(**launch_args)
    
    context = browser.new_context(
        user_agent=USER_AGENT,
        viewport={'width': 1280, 'height': 800},
        ignore_https_errors=True
    )
    return browser, context

def _human_delay(min_s: float = 1.0, max_s: float = 3.0):
    """Sleep for a random amount of time to simulate human behavior."""
    time.sleep(random.uniform(min_s, max_s))

def _determine_job_level(title: str) -> str:
    """Determine job level from job title."""
    title_lower = title.lower()
    if any(k in title_lower for k in ["senior", "lead", "principal", "head", "manager", "director", "chief", "snr", "sr"]):
        return "Senior"
    elif any(k in title_lower for k in ["junior", "trainee", "graduate", "entry", "student", "werkstudent", "praktikum", "intern", "jnr", "jr"]):
        return "Junior"
    return "Mid-Level"

# --- ARBEITSAGENTUR ---
def process_arbeitsagentur_query(page, query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting Arbeitsagentur Scraping for '{query}' ---")
    jobs = []
    
    try:
        url = f"https://www.arbeitsagentur.de/jobsuche/suche?angebotsart=1&was={quote(query)}&wo={quote(config.GERMANY_LOCATION)}&umkreis={config.SEARCH_RADIUS_KM}"
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
        
        # Simple deduplication using filter_existing_job_ids
        existing_ids = supabase_utils.filter_existing_job_ids([l["job_id"] for l in links])
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
                    "level": _determine_job_level(title),
                    "provider": "arbeitsagentur",
                    "description": convert_html_to_markdown(desc_html),
                    "posted_at": None,
                    "source_url": lnk["url"]
                })
            except Exception as e:
                logger.error(f"Error parsing Arbeitsagentur job {lnk['job_id']}: {e}")
                
    except Exception as e:
        logger.error(f"Error hitting Arbeitsagentur: {e}")
    
    return jobs

# --- INDEED ---
def process_indeed_query(page, query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting Indeed Scraping for '{query}' ---")
    jobs = []
    
    try:
        url = f"https://de.indeed.com/jobs?q={quote(query)}&l={quote(config.GERMANY_LOCATION)}&radius={config.SEARCH_RADIUS_KM}"
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
        
        existing_ids = supabase_utils.filter_existing_job_ids(job_ids)
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
                    "level": _determine_job_level(title),
                    "provider": "indeed",
                    "description": convert_html_to_markdown(desc_html),
                    "posted_at": None,
                    "source_url": detail_url
                })
            except Exception as e:
                logger.error(f"Error parsing Indeed job {jid}: {e}")
                
    except Exception as e:
        logger.error(f"Error hitting Indeed: {e}")
            
    return jobs

# --- STEPSTONE ---
def process_stepstone_query(page, query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting StepStone Scraping for '{query}' ---")
    jobs = []
    
    try:
        url = f"https://www.stepstone.de/jobs/{quote(query)}/in-{quote(config.GERMANY_LOCATION)}?radius={config.SEARCH_RADIUS_KM}"
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
            if href:
                # Normalize to absolute URL
                full_url = href if href.startswith('http') else f"https://www.stepstone.de{href}"
                
                if full_url not in [l['url'] for l in links]:
                    # Generate a loose ID
                    # Try regex for exactly the numeric ID before .html or -inline.html
                    match = re.search(r'-(\d+)(?:-inline)?\.html', full_url)
                    if match:
                        job_id = match.group(1)
                    else:
                        # Fallback
                        parts = full_url.split('-')
                        job_id = parts[-1].replace('.html', '').split('?')[0]
                        if job_id == 'inline' and len(parts) > 1:
                            job_id = parts[-2]
                    
                    links.append({"job_id": f"stepstone_{job_id}", "url": full_url})
        
        links = links[:limit]
        
        existing_ids = supabase_utils.filter_existing_job_ids([l["job_id"] for l in links])
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
                    
                article_elem = soup.find("article") or soup.find("main")
                desc_html = str(article_elem) if article_elem else html
                
                jobs.append({
                    "job_id": lnk["job_id"],
                    "company": company,
                    "job_title": title,
                    "location": config.GERMANY_LOCATION,
                    "level": _determine_job_level(title),
                    "provider": "stepstone",
                    "description": convert_html_to_markdown(desc_html)[:5000],
                    "posted_at": None,
                    "source_url": lnk["url"]
                })
            except Exception as e:
                logger.error(f"Error parsing StepStone job {lnk['job_id']}: {e}")
    except Exception as e:
        logger.error(f"Error hitting StepStone: {e}")
            
    return jobs

# --- MEINESTADT ---
def process_meinestadt_query(page, query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting Meinestadt Scraping for '{query}' ---")
    jobs = []
    
    try:
        url = f"https://jobs.meinestadt.de/{quote(config.GERMANY_LOCATION.lower())}/suche?words={quote(query)}&radius={config.SEARCH_RADIUS_KM}"
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
        
        existing_ids = supabase_utils.filter_existing_job_ids([l["job_id"] for l in links])
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
                
                main_elem = soup.find("main") or soup.find("div", {"data-testid": "job-detail-content"})
                desc_html = str(main_elem) if main_elem else html
                
                jobs.append({
                    "job_id": lnk["job_id"],
                    "company": company,
                    "job_title": title,
                    "location": config.GERMANY_LOCATION,
                    "level": _determine_job_level(title),
                    "provider": "meinestadt",
                    "description": convert_html_to_markdown(desc_html)[:5000],
                    "posted_at": None,
                    "source_url": lnk["url"]
                })
            except Exception as e:
                logger.error(f"Error parsing Meinestadt job {lnk['job_id']}: {e}")
    except Exception as e:
        logger.error(f"Error hitting Meinestadt: {e}")
            
    return jobs

# --- JOOBLE ---
def process_jooble_query(page, query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting Jooble Scraping for '{query}' ---")
    jobs = []
    
    try:
        url = f"https://de.jooble.org/Stellenangebote-{quote(query)}/{quote(config.GERMANY_LOCATION)}?radius={config.SEARCH_RADIUS_KM}"
        page.goto(url, wait_until="domcontentloaded", timeout=40000)
        _human_delay(2, 5)
        
        cards = page.locator("article").all()
        job_ids = []
        for c in cards:
            jid = c.get_attribute("data-id")
            if jid and jid not in job_ids:
                job_ids.append(jid)
        
        job_ids = job_ids[:limit]
        
        existing_ids = supabase_utils.filter_existing_job_ids(job_ids)
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
                
                main_elem = soup.find("main") or soup.find("article")
                desc_html = str(main_elem) if main_elem else html
                
                jobs.append({
                    "job_id": jid,
                    "company": "Unknown",
                    "job_title": title,
                    "location": config.GERMANY_LOCATION,
                    "level": _determine_job_level(title),
                    "provider": "jooble",
                    "description": convert_html_to_markdown(desc_html)[:5000],
                    "posted_at": None,
                    "source_url": detail_url
                })
            except Exception as e:
                logger.error(f"Error parsing Jooble job {jid}: {e}")
    except Exception as e:
        logger.error(f"Error hitting Jooble: {e}")
            
    return jobs

# --- WORKWISE ---
def process_workwise_query(page, query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting Workwise Scraping for '{query}' ---")
    jobs = []
    
    try:
        url = f"https://www.workwise.io/jobsuche?q={quote(query)}&location={quote(config.GERMANY_LOCATION)}&radius={config.SEARCH_RADIUS_KM}"
        page.goto(url, wait_until="domcontentloaded", timeout=40000)
        _human_delay(2, 5)
        
        cards = page.locator("a[href*='/job/'], a[href*='/jobs/']").all()
        links = []
        for c in cards:
            href = c.get_attribute("href")
            if href and href not in [l.get('url') for l in links if 'url' in l]:
                # Generate a loose ID
                job_id = href.split('/')[-1].split('?')[0]
                if len(job_id) > 5:
                    full_url = f"https://www.workwise.io{href}" if href.startswith('/') else href
                    links.append({"job_id": f"workwise_{job_id}", "url": full_url})
        
        links = links[:limit]
        
        existing_ids = supabase_utils.filter_existing_job_ids([l["job_id"] for l in links])
        new_links = [l for l in links if l["job_id"] not in existing_ids]
        
        for lnk in new_links:
            try:
                page.goto(lnk["url"], wait_until="domcontentloaded")
                _human_delay(2, 4)
                
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                title_elem = soup.find("h1")
                title = title_elem.text.strip() if title_elem else "Unknown"
                
                main_elem = soup.find("main") or soup.find("div", {"id": "job-description"})
                desc_html = str(main_elem) if main_elem else html

                jobs.append({
                    "job_id": lnk["job_id"],
                    "company": "Unknown",
                    "job_title": title,
                    "location": config.GERMANY_LOCATION,
                    "level": _determine_job_level(title),
                    "provider": "workwise",
                    "description": convert_html_to_markdown(desc_html)[:5000],
                    "posted_at": None,
                    "source_url": lnk["url"]
                })
            except Exception as e:
                logger.error(f"Error parsing Workwise job {lnk['job_id']}: {e}")
    except Exception as e:
        logger.error(f"Error hitting Workwise: {e}")
            
    return jobs

# --- MUSEUMSBUND ---
def process_museumsbund_query(page, query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting Museumsbund Scraping for '{query}' ---")
    jobs = []
    
    try:
        url = "https://www.museumsbund.de/stellenangebote/"
        page.goto(url, wait_until="networkidle", timeout=40000)
        _human_delay(2, 4)
        
        # Accept cookies if banner exists
        try:
            # Based on common patterns or subagent findings
            page.click("button:has-text('Alle akzeptieren'), .cmplz-accept", timeout=3000)
            _human_delay(1, 2)
        except:
            pass

        # Use the search bar
        try:
            page.fill("input.facetwp-search", query)
            page.keyboard.press("Enter")
            # Wait for results to update (FacetWP usually uses AJAX)
            page.wait_for_selector("div.facetwp-template", timeout=10000)
            _human_delay(2, 4)
        except Exception as e:
            logger.warning(f"Could not use search bar on Museumsbund: {e}")

        # Extract links
        # From subagent: article.teaser--stellenangebot and a.teaser__headline-link
        cards = page.locator("article.teaser--stellenangebot a.teaser__headline-link").all()
        links = []
        for c in cards:
            href = c.get_attribute("href")
            if href:
                full_url = href if href.startswith('http') else f"https://www.museumsbund.de{href}"
                # The href usually contains a slug that can serve as an ID
                job_id = href.strip('/').split('/')[-1]
                links.append({"job_id": f"museumsbund_{job_id}", "url": full_url})
        
        links = links[:limit]
        
        existing_ids = supabase_utils.filter_existing_job_ids([l["job_id"] for l in links])
        new_links = [l for l in links if l["job_id"] not in existing_ids]
        
        for lnk in new_links:
            try:
                page.goto(lnk["url"], wait_until="domcontentloaded")
                _human_delay(1, 3)
                
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                # From subagent: h1.content__headline, p.content__organisation, p.content__location, div.content__body
                title_elem = soup.select_one("h1.content__headline")
                title = title_elem.text.strip() if title_elem else "Unknown Title"
                
                company_elem = soup.select_one("p.content__organisation")
                company = company_elem.text.strip() if company_elem else "Unknown Organization"
                
                location_elem = soup.select_one("p.content__location")
                location = location_elem.text.strip() if location_elem else "Germany"
                
                desc_elem = soup.select_one("div.content__body")
                desc_html = str(desc_elem) if desc_elem else html
                
                jobs.append({
                    "job_id": lnk["job_id"],
                    "company": company,
                    "job_title": title,
                    "location": location,
                    "level": _determine_job_level(title),
                    "provider": "museumsbund",
                    "description": convert_html_to_markdown(desc_html),
                    "posted_at": None,
                    "source_url": lnk["url"]
                })
            except Exception as e:
                logger.error(f"Error parsing Museumsbund job {lnk['job_id']}: {e}")
                
    except Exception as e:
        logger.error(f"Error hitting Museumsbund: {e}")
            
    return jobs

# --- XING ---
def process_xing_query(page, query: str, limit: int = 5) -> list:
    logger.info(f"--- Starting Xing Scraping for '{query}' ---")
    jobs = []
    
    try:
        url = f"https://www.xing.com/jobs/search?keywords={quote(query)}&location={quote(config.GERMANY_LOCATION)}"
        page.goto(url, wait_until="domcontentloaded", timeout=40000)
        _human_delay(3, 6)
        
        try:
            page.click("button#consent-accept-button, button[data-testid='accept-all']", timeout=3000)
            _human_delay(1, 2)
        except:
            pass
        
        article_links = page.locator("a[href*='/jobs/api/'], a[href*='/jobs/']").all()
        links = []
        for a in article_links:
            href = a.get_attribute("href")
            if href and '/jobs/' in href and not '/search' in href:
                full_url = href if href.startswith('http') else f"https://www.xing.com{href}"
                job_id = href.split('/')[-1].split('?')[0]
                if len(job_id) > 5 and full_url not in [l['url'] for l in links]:
                    links.append({"job_id": f"xing_{job_id}", "url": full_url})
        
        links = links[:limit]
        
        existing_ids = supabase_utils.filter_existing_job_ids([l["job_id"] for l in links])
        new_links = [l for l in links if l["job_id"] not in existing_ids]
        
        for lnk in new_links:
            try:
                page.goto(lnk["url"], wait_until="domcontentloaded")
                _human_delay(2, 5)
                
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                title_elem = soup.find("h1")
                title = title_elem.text.strip() if title_elem else "Unknown"
                
                company_elem = soup.find("h2") or soup.find("a", {"data-testid": "company-link"})
                company = company_elem.text.strip() if company_elem else "Unknown"
                
                article_elem = soup.find("article") or soup.find("div", {"data-testid": "job-description"}) or soup.find("main")
                desc_html = str(article_elem) if article_elem else html
                
                jobs.append({
                    "job_id": lnk["job_id"],
                    "company": company,
                    "job_title": title,
                    "location": config.GERMANY_LOCATION,
                    "level": _determine_job_level(title),
                    "provider": "xing",
                    "description": convert_html_to_markdown(desc_html)[:5000],
                    "posted_at": None,
                    "source_url": lnk["url"]
                })
            except Exception as e:
                logger.error(f"Error parsing Xing job {lnk['job_id']}: {e}")
    except Exception as e:
        logger.error(f"Error hitting Xing: {e}")
            
    return jobs
