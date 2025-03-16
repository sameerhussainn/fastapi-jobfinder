import pandas as pd
import logging
from linkedin_jobs_scraper import LinkedinScraper
from linkedin_jobs_scraper.events import Events, EventData
from linkedin_jobs_scraper.query import Query, QueryOptions, QueryFilters
from linkedin_jobs_scraper.filters import RelevanceFilters, TimeFilters, RemoteFilters
import os

# Authentication
os.environ["LI_AT_COOKIE"] = "https://github.com/spinlud/py-linkedin-jobs-scraper"  # check section Anonymous vs authenticated session follow the steps

# Initiate the jobs list
jobs = []

def on_data(data: EventData):

    """  Saving data in a dictionary  """

    if data.employment_type == 'Apprenticeship' or data.employment_type == 'Self-employed':
        employement_type = 'other'
    else:
        employement_type = data.employment_type.lower()

    vals = {
        "name": data.title,
        "ats_location": data.location,
        "company_name": data.company,
        "job_apply_url": data.link,
        "general_description": data.description_html,
        "ats_update_date": data.date,
        "job_type": employement_type
    }
    jobs.append(vals)


def on_error(error):

    """  Printing errors if there is any """

    print('[ON_ERROR]', error)


def scrap_linkedin(queries):

    """  Takes a list of search queries  as inputs
            and returns a csv file with all the jobs
             found for those queries     """

    # Initiate the list of queries
    queries_scrapper = []

    # Change root logger level (default is WARN)
    logging.basicConfig(level=logging.INFO)

    scraper = LinkedinScraper(
        chrome_executable_path=None,   # Custom Chrome executable path (e.g. /foo/bar/bin/chromedriver)
        chrome_options=None,   # Custom Chrome options here
        headless=True,   # Overrides headless mode only if chrome_options is None
        max_workers=1,  # How many threads will be spawned to run queries concurrently
        slow_mo=5,   # Slow down the scraper to avoid 'Too many requests (429)' errors
    )

    # Define the queries
    for q in queries:
        queries_scrapper.append(Query(query=q['query'],
                                options=QueryOptions(
                                    locations=[q['location']],
                                    optimize=True,
                                    limit=q['limit'],
                                    filters=QueryFilters(
                                        relevance=RelevanceFilters.RECENT,
                                        time=TimeFilters.DAY,
                                        remote=RemoteFilters.REMOTE))))

    # Add event listeners
    scraper.on(Events.DATA, on_data)
    scraper.on(Events.ERROR, on_error)

    # Start scrapping
    scraper.run(queries_scrapper)

    return jobs


if __name__ == "__main__":

    queries = [{"query": 'Software engineer', "location": 'United States', "limit": 3},
                      {"query": 'Data scientist', "location": 'United States', "limit": 3}]

    jobs=scrap_linkedin(queries)

    # Save the jobs found to csv
    df = pd.DataFrame(jobs)
    df.to_csv('scrapped_jobs.csv', index=False)
