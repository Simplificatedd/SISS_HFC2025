from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd
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
wait = WebDriverWait(driver, 5)  # Wait up to 5 seconds for elements to load

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
            seniority = card.find("p", {"data-cy": "job-card__seniority"}).text.strip()
        except AttributeError:
            seniority = "N/A"
        
        try:
            category = card.find("p", {"data-cy": "job-card__category"}).text.strip()
        except AttributeError:
            category = "N/A"
        
        try:
            # Find the salary info container
            salary_info = card.find("div", {"data-cy": "salary-info"})
            if salary_info:
                # Locate the salary range
                salary_range_div = salary_info.find("div", class_="lh-solid")
                if salary_range_div:
                    # Extract lower and upper salary
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

        jobs.append({
            "Job Title": job_title,
            "Company": company,
            "Location": location,
            "Employment Type": employment_type,
            "Seniority": seniority,
            "Category": category,
            "Salary": salary,
            "Posted Date": posted_date
        })
    
    return jobs

# Initialize the list to store all job postings
all_jobs = []

# Scrape multiple pages
while True:
    try:
        # Scrape the current page
        jobs_on_page = scrape_page()
        all_jobs.extend(jobs_on_page)
        
        # Find and click the "Next" button
        next_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next']"))
        )
        next_button.click()
        time.sleep(2)  # Wait for the next page to load
    except Exception as e:
        print("No more pages or an error occurred:", e)
        break

# Close the browser
driver.quit()

# Save the scraped data to a CSV file
df = pd.DataFrame(all_jobs)
df.to_csv("mycareersfuture_jobs.csv", index=False)

print("Scraping completed. Data saved to mycareersfuture_jobs.csv.")
