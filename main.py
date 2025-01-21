import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from langchain_ollama import OllamaLLM
from sklearn.metrics.pairwise import cosine_similarity
import re

# Disable parallelism for tokenizers
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Model configuration
from config import MODEL

# Define file paths for the CSV datasets
CAREERS_CSV_PATH = "dataset/mycareersfuture_jobs.csv"
SKILLS_CSV_PATH = "dataset/skillsfuture_courses.csv"

# Load data from CSV files
def load_csv_data(csv_path):
    return pd.read_csv(csv_path)

# Extract text for embeddings
def extract_text_from_csv(data, text_columns):
    combined_text = data[text_columns].fillna(" ").apply(" ".join, axis=1)
    return combined_text.tolist()

# Chunk the text for efficient retrieval
def chunk_text(text_list, chunk_size=1000, overlap=200):
    chunks = []
    for text in text_list:
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
    return chunks

# Create embeddings using SentenceTransformer
def create_embeddings(chunks):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(chunks, convert_to_tensor=False)
    return np.array(embeddings)

# Build FAISS index
def build_faiss_index(embeddings):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index

# Search FAISS index with relevance and diversity
def search_faiss_index(query, faiss_index, chunks, model, k=5, diversity_threshold=0.8):
    query_embedding = model.encode([query], convert_to_tensor=False)
    D, I = faiss_index.search(np.array(query_embedding), k * 2)

    selected_chunks = []
    selected_indices = []
    selected_embeddings = []

    for idx in I[0]:
        if len(selected_chunks) >= k:
            break
        chunk = chunks[idx]
        chunk_embedding = model.encode([chunk], convert_to_tensor=False)
        if all(cosine_similarity(
            np.atleast_2d(chunk_embedding), 
            np.atleast_2d(e))[0][0] < diversity_threshold for e in selected_embeddings):
            selected_chunks.append(chunk)
            selected_indices.append(idx)
            selected_embeddings.append(chunk_embedding)

    if len(selected_chunks) < k:
        for idx in I[0][len(selected_chunks):k]:
            selected_chunks.append(chunks[idx])
            selected_indices.append(idx)

    return selected_chunks, selected_indices

# Load datasets
careers_data = load_csv_data(CAREERS_CSV_PATH)
skills_data = load_csv_data(SKILLS_CSV_PATH)

# Extract and process text for embeddings
careers_text_columns = ["Job Title", "Company", "Location", "Employment Type", "Salary"]
skills_text_columns = ["Institution", "Course Title", "Upcoming Date", "Duration", "Training Mode", "Full Fee", "Funded Fee"]

careers_text = extract_text_from_csv(careers_data, careers_text_columns)
skills_text = extract_text_from_csv(skills_data, skills_text_columns)

careers_chunks = chunk_text(careers_text)
skills_chunks = chunk_text(skills_text)

careers_embeddings = create_embeddings(careers_chunks)
skills_embeddings = create_embeddings(skills_chunks)

careers_faiss_index = build_faiss_index(careers_embeddings)
skills_faiss_index = build_faiss_index(skills_embeddings)

print("Data processing and FAISS index creation complete.")

## FEW SHOT PROMPTING

few_shot_examples = """
Example 1:
User's Question: "What are some courses that can help me upskill in data analysis?"
Response: 
Here are some courses that might help you upskill in data analysis:
1. **Advanced Data Analytics with Python**
   - **Institution**: SkillsFuture Academy
   - *Learn advanced Python techniques focusing on big data and visualization.*
2. **Introduction to Data Analytics**
   - **Institution**: DataTech Institute
   - *A beginner-friendly course covering key concepts in data analysis and reporting.*
3. **Data Visualization and Reporting with Tableau**
   - **Institution**: AnalyticsEdge
   - *Master the art of data storytelling by learning Tableau for creating impactful dashboards and visualizations.*

Do any of these courses align with your goals, or would you like to explore other areas?

---

Example 2:
User's Question: "What are some job opportunities for software developers?"
Response: 
Here are the job opportunities you might be interested in:
1. **Full-Stack Developer**
   - **Company**: XYZ Tech  
   - *Develop web applications and collaborate with cross-functional teams.*
2. **Mobile App Developer**
   - **Company**: ABC Innovations  
   - *Create and optimize mobile applications for Android and iOS platforms.*
3. **Backend Engineer**
   - **Company**: CloudWorks Solutions  
   - *Focus on server-side architecture, API development, and database management to support scalable applications.*

Do these roles align with your career goals, or would you like me to refine the suggestions?

---

Example 3:
User's Question: "How can I improve my resume to align with the Full-Stack Developer position at XYZ Tech?"
Response: 
To align your resume with the **Full-Stack Developer** role at **XYZ Tech**, consider the following improvements:
1. **Highlight Relevant Technical Skills**:
   - Emphasize skills like **JavaScript**, **React**, **Node.js**, and **REST APIs**, as they are commonly required for full-stack development.
2. **Showcase Project Experience**:
   - Include projects where you developed full-stack applications, focusing on the technologies and frameworks used, as well as the impact of your work.
3. **Add Metrics to Achievements**:
   - Quantify your accomplishments, e.g., "Developed a web application that increased client engagement by 30%."
4. **Include Collaborative Experience**:
   - Highlight any experience working in cross-functional teams, as collaboration is key in full-stack development roles.

Let me know if you'd like help crafting a tailored resume summary or refining specific sections!

---
Example 4:
User's Question: "How can I improve my resume to align with the Junior Retail Associate position at RECRUIT NOW SINGAPORE PTE. LTD.?"
Response: 
To align your resume with the **Junior Retail Associate** role at **RECRUIT NOW SINGAPORE PTE. LTD.**, consider the following improvements:

1. **Emphasize Retail Experience**:
   - Highlight any roles involving cash handling, customer service, or sales. For example: 
     *"Managed cash transactions and provided excellent customer service at NTUC FairPrice, increasing customer satisfaction ratings by 15%."*

2. **Add Relevant Skills**:
   - Include skills like **Point-of-Sale (POS) systems**, **inventory management**, and **team collaboration** to align with the role's requirements.

3. **Quantify Achievements**:
   - Add metrics to demonstrate your impact, e.g.: *"Reduced inventory discrepancies by 10% through improved stock management techniques."*

4. **Restructure for Clarity**:
   - Use a "Skills" section at the top of your resume to immediately highlight relevant qualifications for retail roles.

Would you like help refining these sections or drafting a tailored summary for this role?

---
"""



# CO-STAR Framework with Few-Shot Prompting
context = """
You are an AI assistant designed to answer questions specifically about job opportunities from MyCareersFuture and courses from SkillsFuture. Your primary goal is to directly answer the user's question based on the context of their query and the datasets provided. You must strictly adhere to the type of information requested—if the user asks for jobs, only provide job-related recommendations; if the user asks for courses, only provide course-related recommendations. Do not mix or include both unless explicitly requested by the user.
"""

outcome = """
1. Directly address the user's question with the information that you have.
2. If the user asks for job recommendations, only list 3 relevant jobs with explanations and avoid mentioning courses unless explicitly requested.
3. If the user asks for course recommendations, only list 3 relevant courses with explanations and avoid mentioning jobs unless explicitly requested.
4. Conclude with a follow-up question to encourage further engagement, but keep it specific to the query type.
"""

resources = """
Use MyCareersFuture for job-related queries and SkillsFuture for course-related queries. If no relevant information is available in the datasets, inform the user politely and offer to refine the query for better results.
"""

examples = """
{few_shot_examples}
"""

time = """
Keep responses precise and focused on the user's query type to avoid overwhelming them with unnecessary information.
"""


def answer_question(query, cv_text, mode, history, model_name=MODEL):
    llm = OllamaLLM(model=MODEL)
    MAX_HISTORY_LENGTH = 10

    if len(history) > MAX_HISTORY_LENGTH:
        history = history[-MAX_HISTORY_LENGTH:]

    # Reset history if a new resume is uploaded
    if cv_text and "resume" in query.lower():
        history = []  # Clear history for a new resume

    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        combined_query = f"""
        The user has uploaded a resume with the following details:
        {cv_text}
        
        The user has asked the following question:
        {query}
        """

        # Determine dataset and fields based on mode
        if mode == "career":
            faiss_index = careers_faiss_index
            chunks = careers_chunks
            data = careers_data
            fields = ["Job Title", "Company", "Location", "Salary", "Job Description", "Link"]
        elif mode == "skill":
            faiss_index = skills_faiss_index
            chunks = skills_chunks
            data = skills_data
            fields = ["Course Title", "Institution", "Duration", "Upcoming Date", "Full Fee", "Funded Fee", "Description", "Link"]

        relevant_chunks, relevant_indices = search_faiss_index(
            query=combined_query,
            faiss_index=faiss_index,
            chunks=chunks,
            model=model,
            k=5
        )

        # Fetch job/course details
        details_list = []
        for idx in relevant_indices[:3]:
            row = data.iloc[idx]
            details = {field: row[field] if field in row else "N/A" for field in fields}
            details_list.append(details)

        # Prepare recommendations
        recommendations = [
            {"title": details["Job Title" if mode == "career" else "Course Title"]}
            for details in details_list
        ]

        # Generate LLM response
        detailed_context = "\n".join(
            [
                f"{details['Job Title' if mode == 'career' else 'Course Title']} at {details['Company' if mode == 'career' else 'Institution']}"
                for details in details_list
            ]
        )

        llm_response = llm(
            f"""
            {context}
            {outcome}
            {examples}
            {time}
            {resources}
            
            User's Resume:
            {cv_text if cv_text else "No resume uploaded."}

            Relevant Context:
            {detailed_context}

            User's Question:
            {query}

            If no resume has been provided, explicitly state that you cannot provide personalized recommendations without reviewing the user's resume. Provide general advice or invite the user to upload their resume for a detailed analysis.

            Answer the user's question specifically without adding extra context. 
            - If the user asks for job recommendations, provide only job recommendations in a concise format. 
            - If the user asks about improving their resume, provide targeted resume improvement suggestions. 
            - If the user asks about courses, provide only relevant courses. 
            - Do not include unrelated information or combine multiple query types unless explicitly requested by the user.
            - Use concise bullet points or numbered lists for clarity.
            - Use Markdown formatting to structure the response.

            If no relevant data is available, politely inform the user and suggest refining their query.
            """
        )



        return history, {
            "text": llm_response,
            "recommendations": recommendations,
        }

    except Exception as e:
        return history, {"text": f"Error: {str(e)}", "recommendations": []}
