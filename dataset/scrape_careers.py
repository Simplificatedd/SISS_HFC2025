import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import signal
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")  # Enable headless mode
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)

driver.maximize_window()

# Open the website
BASE_URL = "https://www.mycareersfuture.gov.sg/search?sortBy=relevancy&page=0"
driver.get(BASE_URL)

# Wait for the page to load
wait = WebDriverWait(driver, 5)

# Initialize the list to store all job postings
all_jobs = []

def save_progress():
    """Save the progress to a CSV file."""
    if all_jobs:
        df = pd.DataFrame(all_jobs)
        df.to_csv("mycareersfuture_jobs_with_description.csv", index=False)
        print("Progress saved to mycareersfuture_jobs_with_description.csv.")

# Handle interruptions (e.g., Ctrl+C)
def signal_handler(sig, frame):
    print("Interrupted! Saving progress...")
    save_progress()
    driver.quit()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Function to scrape job description from the detailed page
def scrape_job_description(job_link):
    driver.get(job_link)  # Navigate to the job detail page
    time.sleep(2)  # Wait for the page to load

    try:
        # Retrieve job description using XPath
        job_description = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/main/div/div/section/div[1]/div[4]/div[2]/section/div").text.strip()
    except Exception as e:
        print(f"Error retrieving job description: {e}")
        job_description = "N/A"

    # Navigate back to the listing page
    driver.back()
    time.sleep(2)  # Wait for the listing page to reload
    print(job_description)
    return job_description

# Function to scrape one page of job postings
def scrape_page():
    soup = BeautifulSoup(driver.page_source, "html.parser")
    job_cards = soup.find_all("a", class_="JobCard__card___22xP3")

    jobs = []
    for card in job_cards:
        try:
            job_title = card.find("span", {"data-testid": "job-card__job-title"}).text.strip()
        except AttributeError:
            job_title = "N/A"

        try:
            job_link = card["href"]
            job_link = f"https://www.mycareersfuture.gov.sg{job_link}"
        except (AttributeError, TypeError):
            job_link = "N/A"

        try:
            company = card.find("p", {"data-testid": "company-hire-info"}).text.strip()
        except AttributeError:
            company = "N/A"

        try:
            location = card.find("p", {"data-cy": "job-card__location"}).text.strip()
        except AttributeError:
            location = "N/A"

        try:
            employment_type = card.find("p", {"data-cy": "job-card__employment-type"}).text.strip()
        except AttributeError:
            employment_type = "N/A"

        try:
            salary_info = card.find("div", {"data-cy": "salary-info"})
            if salary_info:
                salary_range_div = salary_info.find("div", class_="lh-solid")
                if salary_range_div:
                    lower_salary = salary_range_div.find_all("span", class_="dib")[0].text.strip()
                    upper_salary = salary_range_div.find_all("span", class_="dib")[1].text.strip()
                    salary = f"{lower_salary} to {upper_salary}"
                else:
                    salary = "Not specified"
            else:
                salary = "Not specified"
        except Exception as e:
            salary = "Not specified"
            print(f"Error extracting salary: {e}")

        try:
            posted_date = card.find("span", {"data-cy": "job-card-date-info"}).text.strip()
        except AttributeError:
            posted_date = "N/A"

        # Scrape job description from the detailed page
        if job_link != "N/A":
            job_description = scrape_job_description(job_link)
        else:
            job_description = "N/A"

        jobs.append({
            "Job Title": job_title,
            "Link": job_link,
            "Company": company,
            "Location": location,
            "Employment Type": employment_type,
            "Salary": salary,
            "Job Description": job_description
        })

    return jobs

# Scrape multiple pages
try:
    while True:
        try:
            # Scrape the current page
            jobs_on_page = scrape_page()
            all_jobs.extend(jobs_on_page)
            print(f"Scraped {len(jobs_on_page)} jobs on this page.")

            # Check if the current page is page=499 and exit
            if "page=499" in driver.current_url:
                print("Reached page=499. Exiting the loop.")
                break

            # Check if the "Next" button exists
            next_buttons = driver.find_elements(By.XPATH, "//button[@aria-label='Next']")
            if not next_buttons:  # If the "Next" button is not found
                print("No more pages to scrape. Exiting.")
                break

            # Click the "Next" button
            next_button = next_buttons[0]
            next_button.click()
            time.sleep(2)  # Wait for the next page to load
        except Exception as e:
            print(f"Error occurred: {e}. Exiting.")
            break
except Exception as e:
    print(f"Unexpected error: {e}. Exiting.")
finally:
    save_progress()
    driver.quit()

print("Scraping completed.")
