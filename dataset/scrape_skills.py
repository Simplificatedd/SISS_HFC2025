import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import signal
import sys
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)
driver.maximize_window()

# Base URL with query parameters
BASE_URL = "https://www.myskillsfuture.gov.sg/content/portal/en/portal-search/portal-search.html"
QUERY_PARAMS = "?fq=Course_Supp_Period_To_1%3A%5B2025-01-11T00%3A00%3A00Z%20TO%20*%5D&fq=IsValid%3Atrue&q=*%3A*"
START_PARAM = "&start="

# Wait object
wait = WebDriverWait(driver, 10)

# Initialize the list to store all course data
all_courses = []

def save_progress():
    """Save the progress to a CSV file."""
    if all_courses:
        df = pd.DataFrame(all_courses)
        df.to_csv("skillsfuture_courses.csv", index=False)
        print("Progress saved to skillsfuture_courses.csv.")

# Handle interruptions (e.g., Ctrl+C)
def signal_handler(sig, frame):
    print("Interrupted! Saving progress...")
    save_progress()
    driver.quit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def scrape_course_details(course_link):
    """Scrape detailed course information from the course details page."""
    try:
        driver.get(course_link)
        print(f"Navigating to: {course_link}")

        # Wait for the course details to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "col-lg-8")))
        time.sleep(5)  # Ensure all elements are loaded

        # Extract detailed information
        try:
            about_course = driver.find_element(By.XPATH, "//h4[text()='About This Course']/following-sibling::p").text.strip()
        except Exception:
            about_course = "N/A"

        try:
            what_you_learn = driver.find_element(By.XPATH, "//h4[text()=\"What You'll Learn\"]/following-sibling::p").text.strip()
        except Exception:
            what_you_learn = "N/A"

        try:
            min_requirement = driver.find_element(By.XPATH, "//h4[text()='Minimum Entry Requirement']/following-sibling::p").text.strip()
        except Exception:
            min_requirement = "N/A"

        try:
            full_fee = driver.find_element(By.XPATH, "/html/body/main/div[1]/div[1]/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div[1]/div/strong").text.strip()
        except Exception:
            full_fee = "N/A"

        # Scrape "After SkillsFuture Funding"
        try:
            time.sleep(2)
            funded_fee_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "strong[data-bind*='courseDetail.extCourseRefNo']"))
            )
            funded_fee = funded_fee_element.text.strip()
        except Exception as e:
            funded_fee = "N/A"
            print(f"Error retrieving funded fee: {e}")
        print(f"About This Course: {about_course}")
            

        return about_course, what_you_learn, min_requirement, full_fee, funded_fee
    

    except Exception as e:
        print(f"Error retrieving details for {course_link}: {e}")
        return "N/A", "N/A", "N/A", "N/A", "N/A"

def scrape_page():
    """Scrapes one page of courses."""
    courses = []
    soup = BeautifulSoup(driver.page_source, "html.parser")
    course_cards = soup.find_all("div", class_="card")

    if not course_cards:
        print("No course cards found on the page.")
        return courses

    for card in course_cards:
        try:
            institution = card.find("div", class_="course-provider").text.strip() if card.find("div", class_="course-provider") else "N/A"
            course_title = card.find("h5", class_="card-title").find("a").text.strip() if card.find("h5", class_="card-title") else "N/A"
            course_link = f"https://www.myskillsfuture.gov.sg{card.find('h5', class_='card-title').find('a')['href']}" if card.find("h5", class_="card-title") else "N/A"

            try:
                upcoming_date = card.find("strong", {"data-bind": "text: $Util.formatDate(Course_Start_Date_Nearest)"}).text.strip()
            except AttributeError:
                upcoming_date = "N/A"

            try:
                duration = card.find("div", class_="card-course-duration-holder").find("span").text.strip()
            except AttributeError:
                duration = "N/A"

            try:
                training_mode = card.find("div", class_="card-course-type-holder").find("span").text.strip()
            except AttributeError:
                training_mode = "N/A"

            if course_link != "N/A":
                about_course, what_you_learn, min_requirement, full_fee, funded_fee = scrape_course_details(course_link)
                driver.back()
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card")))
            else:
                about_course = what_you_learn = min_requirement = full_fee = funded_fee = "N/A"

            if course_title != "N/A":
                courses.append({
                    "Institution": institution,
                    "Course Title": course_title,
                    "Link": course_link,
                    "Upcoming Date": upcoming_date,
                    "Duration": duration,
                    "Training Mode": training_mode,
                    "Full Fee": full_fee,
                    "Funded Fee": funded_fee,
                    "About This Course": about_course,
                    "What You'll Learn": what_you_learn,
                    "Minimum Entry Requirement": min_requirement
                })

        except Exception as e:
            print(f"Error processing course card: {e}")

    return courses

def scrape_all_pages():
    start_index = 0
    while True:
        try:
            url = f"{BASE_URL}{QUERY_PARAMS}{START_PARAM}{start_index}"
            print(f"Scraping URL: {url}")
            driver.get(url)
            print("Waiting for the page to load...")
            time.sleep(10)

            WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card")))

            courses_on_page = scrape_page()
            if not courses_on_page:
                print("No more courses to scrape. Exiting.")
                break

            all_courses.extend(courses_on_page)
            print(f"Scraped {len(courses_on_page)} courses on this page.")

            start_index += 24
        except Exception as e:
            print(f"An error occurred: {e}. Exiting.")
            break

if __name__ == "__main__":
    try:
        scrape_all_pages()
    except Exception as e:
        print(f"Unexpected error: {e}. Exiting.")
    finally:
        save_progress()
        driver.quit()
        sys.exit(0)
