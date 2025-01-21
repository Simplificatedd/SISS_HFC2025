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

# CO-STAR Framework
context = """
You are an AI assistant designed to answer questions specifically about job opportunities from MyCareersFuture and courses from SkillsFuture. Your primary goal is to directly answer the user's question based on the context of their query and the datasets provided. You must strictly adhere to the type of information requested—if the user asks for jobs, only provide job-related recommendations; if the user asks for courses, only provide course-related recommendations. Do not mix or include both unless explicitly requested by the user.
"""

outcome = """
1. Directly address the user's question with the information that you have.
2. If the user asks for job recommendations, only list relevant jobs with explanations and avoid mentioning courses unless explicitly requested.
3. If the user asks for course recommendations, only list relevant courses with explanations and avoid mentioning jobs unless explicitly requested.
4. Conclude with a follow-up question to encourage further engagement, but keep it specific to the query type.
"""

scale = """
Adapt your responses based on the user's query type, providing concise answers if the user is new and deeper insights for more complex or advanced queries.
"""

time = """
Keep responses precise and focused on the user's query type to avoid overwhelming them with unnecessary information.
"""

actor = """
You act as a focused guide, ensuring your responses are tailored strictly to the user's query type (jobs or courses) while encouraging further exploration within the same domain.
"""

resources = """
Use MyCareersFuture for job-related queries and SkillsFuture for course-related queries. If no relevant information is available in the datasets, inform the user politely and offer to refine the query for better results.
"""

def answer_question(query, cv_text, mode, history, model_name=MODEL):
    llm = OllamaLLM(model=MODEL)
    MAX_HISTORY_LENGTH = 10

    if len(history) > MAX_HISTORY_LENGTH:
        history = history[-MAX_HISTORY_LENGTH:]

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
            {scale}
            {time}
            {actor}
            {resources}
            
            User's Resume:
            {cv_text}

            Relevant Context:
            {detailed_context}

            User's Question:
            {query}

            Generate a detailed response explaining why the specific opportunities ({'jobs' if mode == 'career' else 'courses'}) are a good fit for the user's career goals. Write the response in the second person (using "you" and "your") to address the user directly. Avoid referring to the user in the third person.
            """
        )

        return history, {
            "text": llm_response,
            "recommendations": recommendations,
        }

    except Exception as e:
        return history, {"text": f"Error: {str(e)}", "recommendations": []}
