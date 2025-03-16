from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from scraper import scrape_indeed_jobs, scrape_linkedin_jobs, filter_relevant_jobs
from transformers import pipeline
from transformers import pipeline
import numpy as np
from numpy.linalg import norm


app = FastAPI()

# Define request model
class JobSearchRequest(BaseModel):
    position: str
    experience: Optional[str] = None
    salary: Optional[str] = None
    jobNature: Optional[str] = None
    location: str
    skills: List[str]

# Define response model
class JobListing(BaseModel):
    job_title: str
    company: str
    location: str
    experience: Optional[str] = "Not specified"
    salary: Optional[str] = "Not mentioned"
    apply_link: str


@app.post("/search_jobs/", response_model=List[JobListing])
async def search_jobs(request: JobSearchRequest):
    """Receives job search criteria and scrapes jobs from LinkedIn & Indeed."""

    indeed_jobs = scrape_indeed_jobs(request.position, request.location)
    linkedin_jobs = scrape_linkedin_jobs(request.position, request.location)

    all_jobs = indeed_jobs + linkedin_jobs
    relevant_jobs = filter_relevant_jobs(all_jobs, request.position)

    job_listings = [
        JobListing(
            job_title=job["job_title"],
            company=job["company"],
            location=job["location"],
            experience=job.get("experience", "Not specified"),
            salary=job.get("salary", "Not mentioned"),
            apply_link=job["apply_link"]
        ) for job in all_jobs
    ]

    return job_listings
