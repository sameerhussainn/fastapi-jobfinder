import csv
import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime

def get_url(position, location):
    """Generate the Indeed job search URL"""
    template = 'https://www.indeed.com/jobs?q={}&l={}'
    position = position.replace(' ', '+')
    location = location.replace(' ', '+')
    return template.format(position, location)

def get_record(card):
    """Extract job data from a single Indeed job card"""
    try:
        job_title = card.h2.a.get('title')
        company = card.find('span', class_='companyName').text.strip()
        location = card.find('div', class_='companyLocation').text.strip()
        post_date = card.find('span', class_='date').text.strip()
        summary = card.find('div', class_='job-snippet').text.strip().replace('\n', ' ')
        job_url = 'https://www.indeed.com' + card.h2.a.get('href')

        # Salary (if available)
        salary_tag = card.find('span', class_='salary-snippet')
        salary = salary_tag.text.strip() if salary_tag else 'N/A'

        return (job_title, company, location, post_date, summary, salary, job_url)
    
    except AttributeError:
        return None  # Skip the job if data is missing

def main(position, location):
    """Scrape Indeed job listings for a given position and location"""
    records = []
    url = get_url(position, location)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    while url:
        print(f"Fetching: {url}")
        response = requests.get(url, headers=headers)
        
        # Check for request failure
        if response.status_code != 200:
            print(f"Failed to fetch page: {response.status_code}")
            break
        
        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.find_all('div', class_='cardOutline')  # Updated class

        if not cards:
            print("No job listings found on the page.")
            break
        
        for card in cards:
            record = get_record(card)
            if record:
                records.append(record)

        # Find "Next" button and get the next page URL
        try:
            next_page = soup.find('a', {'aria-label': 'Next'})
            if next_page:
                url = 'https://www.indeed.com' + next_page.get('href')
                time.sleep(5)  # Delay to avoid bot detection
            else:
                break
        except AttributeError:
            break
    
    # Save results to CSV
    with open('results.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Job Title', 'Company', 'Location', 'Post Date', 'Summary', 'Salary', 'Job URL'])
        writer.writerows(records)

    print(f"\nScraping complete! Found {len(records)} jobs.")

# Run the scraper
main('Full Stack Developer', 'Islamabad')
