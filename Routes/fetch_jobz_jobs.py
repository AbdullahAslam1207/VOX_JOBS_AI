import requests
from bs4 import BeautifulSoup
import json
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36"
}

# Base URLs for all cities
CITY_URLS = {
    "lahore": "https://www.jobz.pk/jobs_in_lahore/",
    "karachi": "https://www.jobz.pk/jobs_in_karachi/",
    "islamabad": "https://www.jobz.pk/jobs_in_islamabad/",
    "rawalpindi": "https://www.jobz.pk/jobs_in_rawalpindi/"
}

def get_soup(url):
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def scrape_page(url):
    """Scrape all job entries from a single listing page."""
    jobs_data = []
    soup = get_soup(url)
    main_div = soup.find("div", class_="first_big_4col")

    for row in main_div.find_all("div", class_="row_container", recursive=False):
        cell1 = row.find("div", class_="cell1")
        if not cell1:
            continue
        
        link_tag = cell1.find("a", href=True)
        if not link_tag:
            continue
        
        job_url = link_tag["href"]
        job_entry = {
            "title": cell1.get_text(" ", strip=True),
            "job_url": job_url,
            "details": {}
        }
        
        try:
            # Scrape detail page
            detail_soup = get_soup(job_url)
            job_detail_div = detail_soup.find("div", class_="job_detail")
            
            if job_detail_div:
                for row_detail in job_detail_div.find_all("div", class_="row_job_detail", recursive=False):
                    divs = row_detail.find_all("div", recursive=False)
                    if len(divs) >= 2:
                        key = divs[0].get_text(" ", strip=True).rstrip(":")
                        value = divs[1].get_text(" ", strip=True)
                        links = [a["href"] for a in divs[1].find_all("a", href=True)]
                        
                        if links:
                            job_entry["details"][key] = {
                                "value": value,
                                "links": links
                            }
                        else:
                            job_entry["details"][key] = value
            
            print(f"Scraped: {job_url}")
            time.sleep(1)
        
        except Exception as e:
            print(f"Failed {job_url}: {e}")
        
        jobs_data.append(job_entry)
    
    return jobs_data, soup

# ---------------------------
# MAIN SCRAPER (for all cities)
# ---------------------------
def fetch_jobz_jobs():
    all_jobs = {}

    for city, base_url in CITY_URLS.items():
        city_jobs = []

        # Scrape page 1
        jobs, soup1 = scrape_page(base_url)
        city_jobs.extend(jobs)

        # Find pagination links (grab page 2 only)
        paging_div = soup1.find("div", class_="paging")
        if paging_div:
            for a in paging_div.find_all("a", href=True):
                if "active" in a.get("class", []):
                    continue  # skip current page
                page_url = a["href"]
                
                if page_url.endswith("-1/"):  # only page 2
                    jobs, _ = scrape_page(page_url)
                    city_jobs.extend(jobs)
                    break
        
        all_jobs[city] = city_jobs
        print(f"Finished {city}: {len(city_jobs)} jobs")

    # Save results
    with open("Scraped_Data/jobs_jobz.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    print("Scraping complete.")
    return all_jobs
