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
BASE_URL = "https://www.myskillsfuture.gov.sg/content/portal/en/portal-search/portal-search.html?fq=Course_Supp_Period_To_1%3A%5B2025-01-11T00%3A00%3A00Z%20TO%20*%5D&fq=IsValid%3Atrue&q=*%3A*"
driver.get(BASE_URL)

# Wait for the page to load
wait = WebDriverWait(driver, 10)

# Function to scrape one page of course details
def scrape_page():
    soup = BeautifulSoup(driver.page_source, "html.parser")
    course_cards = soup.find_all("div", class_="card")  # Locate all course cards

    courses = []
    for card in course_cards:
        try:
            # Skip empty or placeholder cards
            if not card.find("div", class_="course-provider"):
                continue

            # Extract institution name
            institution = card.find("div", class_="course-provider").text.strip()
        except AttributeError:
            institution = "N/A"

        try:
            # Extract course title
            course_title = card.find("h5", class_="card-title").find("a").text.strip()
        except AttributeError:
            course_title = "N/A"

        try:
            # Extract course link
            course_link = card.find("h5", class_="card-title").find("a")["href"]
            course_link = f"https://www.myskillsfuture.gov.sg{course_link}"  # Append base URL
        except (AttributeError, TypeError):
            course_link = "N/A"

        try:
            # Extract upcoming course date
            upcoming_date = card.find("strong", {"data-bind": "text: $Util.formatDate(Course_Start_Date_Nearest)"}).text.strip()
        except AttributeError:
            upcoming_date = "N/A"

        try:
            # Extract course duration
            duration = card.find("div", class_="card-course-duration-holder").find("span").text.strip()
        except AttributeError:
            duration = "N/A"

        try:
            # Extract mode of training
            training_mode = card.find("div", class_="card-course-type-holder").find("span").text.strip()
        except AttributeError:
            training_mode = "N/A"

        try:
            # Extract full course fee
            full_fee = card.find("p", {"data-bind": "text: '$'+Tol_Cost_of_Trn_Per_Trainee"}).text.strip()
        except AttributeError:
            full_fee = "N/A"

        try:
            # Extract fee after SkillsFuture funding
            funded_fee = card.find("p", {"data-bind": "attr : { id : EXT_Course_Ref_Nos[0]}"}).text.strip()
        except AttributeError:
            funded_fee = "N/A"

        # Append only if the course title is valid (to exclude placeholders)
        if course_title != "N/A":
            courses.append({
                "Institution": institution,
                "Course Title": course_title,
                "Link": course_link,
                "Upcoming Date": upcoming_date,
                "Duration": duration,
                "Training Mode": training_mode,
                "Full Fee": full_fee,
                "Funded Fee": funded_fee
            })

    return courses


# Initialize the list to store all course data
all_courses = []

# Scrape multiple pages
while True:
    try:
        # Scrape the current page
        print("Scraping current page...")
        courses_on_page = scrape_page()
        all_courses.extend(courses_on_page)
        print(f"Scraped {len(courses_on_page)} courses on this page.")

        # Check if the "Next" button itself is clickable
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.page-link[aria-label='View next page']"))
            )
            print("Navigating to the next page...")
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(3)  # Wait for the next page to load
        except:
            print("The 'Next' button is not clickable, likely disabled. Exiting.")
            break
    except Exception as e:
        print("No more pages or an error occurred:", e)
        break

# Close the browser
driver.quit()

# Save the scraped data to a CSV file
df = pd.DataFrame(all_courses)
df.to_csv("skillsfuture_courses.csv", index=False)

print("Scraping completed. Data saved to skillsfuture_courses.csv.")
