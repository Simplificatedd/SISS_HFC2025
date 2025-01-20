import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from langchain_ollama import OllamaLLM
from sklearn.metrics.pairwise import cosine_similarity

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
You are an AI assistant designed to answer questions about job opportunities from MyCareersFuture and courses from SkillsFuture. Your primary goal is to directly answer the user's question accurately and concisely. If the question relates to job or course recommendations, provide the most relevant options.
If a question falls outside the domain of jobs or courses, politely decline to answer using a single sentence.
"""

outcome = """
1. Directly answer the user's question based on the provided information.
2. Conclude with a follow-up question to encourage further exploration.
"""

scale = """
Adapt responses based on the complexity of the query. Provide simple answers for beginners and deeper insights for advanced users.
"""

time = """
Keep responses concise and relevant to avoid overwhelming the user.
"""

actor = """
You act as a guide, providing tailored advice and follow-up suggestions to help users achieve their goals.
"""

resources = """
Base your answers on the MyCareersFuture and SkillsFuture datasets. If sufficient information is unavailable, inform the user.
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
        if "career" in mode:
            faiss_index = careers_faiss_index
            chunks = careers_chunks
            data = careers_data
            fields = ["Job Title", "Company", "Location", "Salary", "Link"]
        elif "skill" in mode:
            faiss_index = skills_faiss_index
            chunks = skills_chunks
            data = skills_data
            fields = ["Course Title", "Institution", "Duration", "Link"]

        relevant_chunks, relevant_indices = search_faiss_index(
            query=combined_query,
            faiss_index=faiss_index,
            chunks=chunks,
            model=model,
            k=5
        )

        # Fetch job/course details
        job_details = []
        for idx in relevant_indices[:3]:
            row = data.iloc[idx]
            details = {field: row.get(field, "N/A") for field in fields}
            details["title"] = f"<a href='{details.get('Link', '#')}' target='_blank'>{details.get('Course Title' if 'skill' in mode else 'Job Title')}</a>"
            job_details.append(details)

        # Build the first paragraph with hyperlinks embedded
        if "career" in mode:
            first_paragraph = (
                f"Based on your background and career goals, here are some opportunities that match your skills and experience: "
                f"{job_details[0]['title']} at {job_details[0]['Company']} (Location: {job_details[0]['Location']}, Salary: {job_details[0]['Salary']}), "
                f"{job_details[1]['title']} at {job_details[1]['Company']} (Location: {job_details[1]['Location']}, Salary: {job_details[1]['Salary']}), and "
                f"{job_details[2]['title']} at {job_details[2]['Company']} (Location: {job_details[2]['Location']}, Salary: {job_details[2]['Salary']})."
            )
        elif "skill" in mode:
            first_paragraph = (
                f"Based on your background and career goals, here are some courses that match your interests and experience: "
                f"{job_details[0]['title']} by {job_details[0]['Institution']} (Duration: {job_details[0]['Duration']}), "
                f"{job_details[1]['title']} by {job_details[1]['Institution']} (Duration: {job_details[1]['Duration']}), and "
                f"{job_details[2]['title']} by {job_details[2]['Institution']} (Duration: {job_details[2]['Duration']})."
            )

        # Generate additional insights using retrieved details
        detailed_context = "\n".join(
            [
                f"{details['title']} at {details['Company']} (Location: {details['Location']}, Salary: {details['Salary']})"
                if "career" in mode
                else f"{details['title']} by {details['Institution']} (Duration: {details['Duration']})"
                for details in job_details
            ]
        )

        # Update the LLM prompt to explicitly use direct addressing
        additional_insights = llm(
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

            Explain why these specific opportunities are a good fit for you and your career goals. Avoid referring to the user in the third person. Use 'you' and 'your' throughout the explanation.
            """
        )

        # Combine into one final response
        final_response = f"{first_paragraph}<br><br>{additional_insights}"

        history.append(("Chatbot", final_response))
        return history, final_response  # Return combined response

    except Exception as e:
        return history, f"Error: {str(e)}"
