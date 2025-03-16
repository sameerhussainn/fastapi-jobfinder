import requests
import json
import sys
from bs4 import BeautifulSoup
import time as tm
from urllib.parse import quote
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from datetime import datetime, timedelta


def load_config(file_name):
    """ Load the config file """
    with open(file_name) as f:
        return json.load(f)


def get_with_retry(url, config, retries=3, delay=1):
    """ Fetch the URL with retries and delay """
    for i in range(retries):
        try:
            response = requests.get(url, headers=config['headers'], timeout=5)
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.Timeout:
            print(f"Timeout for URL: {url}. Retrying in {delay}s...")
            tm.sleep(delay)
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

        job = {
            'title': title,
            'company': company.text.strip() if company else 'Unknown',
            'location': location.text.strip() if location else 'Unknown',
            'date': date,
            'job_url': job_url
        }
        joblist.append(job)
    return joblist


def safe_detect(text):
    """ Detect language safely """
    try:
        return detect(text)
    except LangDetectException:
        return 'en'


def remove_irrelevant_jobs(joblist, config):
    """ Remove jobs based on filtering conditions from config.json """
    filtered_jobs = [
        job for job in joblist if not any(
            word.lower() in job['title'].lower() for word in config['title_exclude']
        ) and any(
            word.lower() in job['title'].lower() for word in config['title_include']
        )
    ]
    return filtered_jobs


def get_jobcards(config):
    """ Scrape job cards from LinkedIn """
    all_jobs = []
    for query in config['search_queries']:
        keywords = quote(query['keywords'])
        location = quote(query['location'])

        for i in range(config['pages_to_scrape']):
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords}&location={location}&start={i * 25}"
            print(f"Fetching: {url}")
            soup = get_with_retry(url, config)
            jobs = transform(soup)
            all_jobs.extend(jobs)
    
    print(f"\nTotal jobs scraped: {len(all_jobs)}")
    filtered_jobs = remove_irrelevant_jobs(all_jobs, config)
    print(f"Total jobs after filtering: {len(filtered_jobs)}\n")

    return filtered_jobs


def display_jobs(jobs):
    """ Display jobs in the terminal """
    if not jobs:
        print("No jobs found!")
        return

    print("\n--- Job Listings ---\n")
    for idx, job in enumerate(jobs, start=1):
        print(f"{idx}. {job['title']} at {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Date: {job['date']}")
        print(f"   URL: {job['job_url']}\n")


def main(config_file):
    start_time = tm.perf_counter()

    config = load_config(config_file)
    jobs = get_jobcards(config)
    display_jobs(jobs)

    end_time = tm.perf_counter()
    print(f"\nScraping finished in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    config_file = "config.json"
    if len(sys.argv) == 2:
        config_file = sys.argv[1]

    main(config_file)
