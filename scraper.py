import requests
import json
import random
import time
from bs4 import BeautifulSoup
from urllib.parse import quote
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from transformers import pipeline
import numpy as np
from numpy.linalg import norm

similarity_model = pipeline("feature-extraction", model="distilbert-base-uncased")

# ScraperAPI Key (Enable "Premium Proxy Mode" in ScraperAPI settings)
API_KEY = "5c57a388db893325850a3dae3a66eda4"

# User-Agent rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
]

def get_with_retry(url, headers, retries=3, delay=1):
    """ Fetch the URL with retries and delay """
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=5)
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.Timeout:
            print(f"Timeout for URL: {url}. Retrying in {delay}s...")
            time.sleep(delay)
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
    return None

def transform(soup):
    """ Extract job details from the LinkedIn job listing page """
    joblist = []
    if not soup:
        print("No data found on the page.")
        return joblist

    divs = soup.find_all('div', class_='base-search-card__info')
    for item in divs:
        title = item.find('h3').text.strip()
        company = item.find('a', class_='hidden-nested-link')
        location = item.find('span', class_='job-search-card__location')
        parent_div = item.parent
        entity_urn = parent_div.get('data-entity-urn', '')
        job_posting_id = entity_urn.split(':')[-1] if entity_urn else 'N/A'
        job_url = f'https://www.linkedin.com/jobs/view/{job_posting_id}/'

        date_tag = item.find('time', class_='job-search-card__listdate')
        date = date_tag['datetime'] if date_tag else 'Unknown Date'

        # Extracting additional details
        experience_tag = item.find('span', class_='job-search-card__experience')
        salary_tag = item.find('span', class_='job-search-card__salary-info')

        experience = experience_tag.text.strip() if experience_tag else "Not specified"
        salary = salary_tag.text.strip() if salary_tag else "Not mentioned"

        job = {
            'job_title': title,
            'company': company.text.strip() if company else 'Unknown',
            'location': location.text.strip() if location else 'Unknown',
            'experience': experience,
            'salary': salary,
            'apply_link': job_url
        }
        joblist.append(job)
    return joblist


def scrape_linkedin_jobs(position, location):
    """ Scrapes LinkedIn jobs """
    keywords = quote(position)
    location = quote(location)
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords}&location={location}"
    
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    soup = get_with_retry(url, headers)
    
    if not soup:
        return []
    
    return transform(soup)

def scrape_indeed_jobs(position, location):
    """ Scrapes Indeed jobs and extracts job title, company, location, and apply link. """
    indeed_url = f"https://pk.indeed.com/jobs?q={position}&l={location}"
    proxy_url = f"http://api.scraperapi.com/?api_key={API_KEY}&url={indeed_url}"
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    try:
        response = requests.get(proxy_url, headers=headers)
        if response.status_code != 200:
            print(f"⚠️ Failed to retrieve Indeed jobs: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        job_cards = soup.find_all("div", class_="job_seen_beacon")
        print(f"Found {len(job_cards)} Indeed jobs")

        jobs = []
        for job in job_cards[:5]:
            # print(job.prettify())  # Debugging: Print full job card structure

            title_element = job.find("h2")
            company_element = job.find("span", {"data-testid": "company-name"})
            location_element = job.find("div", {"data-testid": "text-location"})
            link_element = job.find("a", href=True)

            title = title_element.text.strip() if title_element else "No title"
            company = company_element.text.strip() if company_element else "Unknown"
            location = location_element.text.strip() if location_element else "Unknown"
            link = f"https://pk.indeed.com{link_element['href']}" if link_element else "No link"

            jobs.append({
                "job_title": title,
                "company": company,
                "location": location,
                "apply_link": link
            })

        time.sleep(random.uniform(2, 4))
        return jobs

    except Exception as e:
        print("Error scraping Indeed:", e)
        return []


def compute_similarity(text1, text2):
    """Compute cosine similarity between two texts"""
    import numpy as np
    from numpy.linalg import norm

    vec1 = np.array(similarity_model(text1)[0]).mean(axis=0)
    vec2 = np.array(similarity_model(text2)[0]).mean(axis=0)

    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def filter_relevant_jobs(jobs, user_query):
    """Filter jobs based on relevance to user criteria using LLM"""
    filtered_jobs = []
    for job in jobs:
        job_text = f"{job['job_title']} at {job['company']} in {job['location']}"
        relevance_score = compute_similarity(job_text, user_query)

        if relevance_score > 0.7:  # Adjust threshold as needed
            job["relevance_score"] = relevance_score  # Add score for debugging
            filtered_jobs.append(job)

    return filtered_jobs

if __name__ == "__main__":
    position = "Software Engineer"
    location = "Islamabad"

    linkedin_jobs = scrape_linkedin_jobs(position, location)
    indeed_jobs = scrape_indeed_jobs(position, location)

    all_jobs = linkedin_jobs + indeed_jobs
    print(f"Total jobs found: {len(all_jobs)}")
    print(all_jobs)
