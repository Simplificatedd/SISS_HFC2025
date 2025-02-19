# SISS_HFC2025
Submission for Hack For Cities 2025
Team Name: Singapore Institute of Social Sciences

## Project Description  

### Overview  
This project proposes an AI-driven solution to bridge the gap between workforce development and the evolving demands of smart city industries. By leveraging a Retrieval-Augmented Generation (RAG) system integrated with Generative AI, the solution aims to deliver personalised career assistance and skill development recommendations.  

The core of the solution is a chatbot that analyses user resumes to extract skills, qualifications, and experiences. It connects users with relevant job opportunities and upskilling courses by utilizing datasets from **CareersFuture** and **SkillsFuture Singapore**. The chatbot also addresses career-related inquiries, offering tailored advice to help users adapt to the dynamic needs of smart city enterprises.  

### Problem it Solves  
In rapidly evolving industries, individuals often struggle with:  
- Identifying skill gaps and relevant job opportunities.  
- Accessing personalised career guidance.  
- Adapting to the skill demands of smart city economies.  

Governments face challenges in aligning workforce capabilities with industry requirements to promote sustainable economic growth and reduce unemployment.  

This solution directly addresses these challenges by:  
1. Enabling individuals to understand their current capabilities and map them to industry needs.  
2. Guiding users towards targeted skill development using SkillsFuture courses.  
3. Assisting governments in workforce alignment efforts, fostering long-term growth and innovation.  

By empowering citizens with career tools tailored to a smart city context, this project contributes to a more adaptive and future-ready workforce.  


---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Simplificatedd/SISS_HFC2025.git
cd SISS_HFC2025
```

### 2. Set Up a Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

Ensure you have `pip` installed. Then, install the required packages:

```bash
pip install -r requirements.txt
```

### 4. Set Node.js to version 16

If you don’t have nvm installed, you can install it by following the instructions on its GitHub page.
Or you can use curl:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
```

Install Node.js version 16:

```bash
nvm install 16
```

Switch to Node.js version 16:

```bash
nvm use 16
```

Verify installation:
```bash
node -v
```
v16.20.2

---

## Usage Guide
### 1. Run the Application

Start the application:

```bash
python app.py
```

Create another terminal and go into the chatbot directory:
```bash
cd chatbot
```

Start the web UI:
```bash
npm start
```

### 2. Using the Application
- **Toggle Between Career or Course results**:
  - Click on the toggle switch on the top right to toggle between career or course results.

- **Resume Parsing**:
  - Upload your resume through the chatbot interface.
  - The system will extract your skills and qualifications.

- **Career Recommendations**:
  - Based on your extracted skills, the chatbot will recommend relevant job opportunities from the CareersFuture dataset.

- **Course Recommendations**:
  - The chatbot will suggest SkillsFuture courses to address any identified skill gaps.

- **Career Inquiries**:
  - Ask the chatbot any career-related questions for personalized advice, such as "What courses should I take to boost my resume?".


---

## Contributors

- **Cheong Shu Yin**  
- **Raven Tang**  
- **Nadhirah Binti Ayub Khan**  
- **Low Yi San**  


---

## Additional Notes

Limitations:
- The project may have limitations based on the dataset used and the implemented functionalities.
  
Future Improvements:
- Enhance the application's features based on user feedback.
- Update dependencies regularly to incorporate the latest improvements and security patches.

