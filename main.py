import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from langchain_ollama import OllamaLLM
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
os.environ["TOKENIZERS_PARALLELISM"] = "false"


# Model
from config import MODEL 

# Define file paths for the CSV datasets
CAREERS_CSV_PATH = "dataset/mycareersfuture_jobs.csv"
SKILLS_CSV_PATH = "dataset/skillsfuture_courses.csv"

# Load data from CSV files
def load_csv_data(csv_path):
    return pd.read_csv(csv_path)

# Step 1: Extract text from CSV data for embeddings
def extract_text_from_csv(data, text_columns):
    combined_text = data[text_columns].fillna("").apply(" ".join, axis=1)
    return combined_text.tolist()

# Step 2: Chunk the text for efficient retrieval (optional for large datasets)
def chunk_text(text_list, chunk_size=1000, overlap=200):
    chunks = []
    for text in text_list:
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
    return chunks

# Step 3: Create embeddings for each chunk using SentenceTransformer
def create_embeddings(chunks):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(chunks, convert_to_tensor=False)
    return np.array(embeddings)

# Step 4: Build FAISS index
def build_faiss_index(embeddings):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index

# Step 5: Search for relevant chunks in FAISS index
def search_faiss_index(query, faiss_index, chunks, model, k=5, diversity_threshold=0.8):
    """
    Enhanced function to search FAISS index with better relevance and diversity.
    :param query: The user query as a string.
    :param faiss_index: The FAISS index.
    :param chunks: The text chunks corresponding to the index.
    :param model: The embedding model (e.g., SentenceTransformer).
    :param k: Number of results to retrieve.
    :param diversity_threshold: Minimum cosine similarity between results for diversity.
    :return: List of relevant and diverse chunks.
    """
    # Generate embedding for the query
    query_embedding = model.encode([query], convert_to_tensor=False)
    
    # Search FAISS index
    D, I = faiss_index.search(np.array(query_embedding), k * 2)  # Retrieve more results initially for diversity

    # Filter results for diversity
    selected_chunks = []
    selected_embeddings = []

    for idx in I[0]:
        if len(selected_chunks) >= k:
            break
        chunk = chunks[idx]
        chunk_embedding = model.encode([chunk], convert_to_tensor=False)
        
        # Check for diversity: compare with already selected chunks
        if all(cosine_similarity(
                np.atleast_2d(chunk_embedding), 
                np.atleast_2d(e))[0][0] < diversity_threshold for e in selected_embeddings):
            selected_chunks.append(chunk)
            selected_embeddings.append(chunk_embedding)
    
    # If diversity filtering reduces results, fallback to the most similar ones
    if len(selected_chunks) < k:
        for idx in I[0][len(selected_chunks):k]:
            selected_chunks.append(chunks[idx])

    return selected_chunks



# Load and process datasets
careers_data = load_csv_data(CAREERS_CSV_PATH)
skills_data = load_csv_data(SKILLS_CSV_PATH)

# Specify columns to use for embeddings
careers_text_columns = ["Job Title", "Company", "Location", "Employment Type", "Salary"]
skills_text_columns = ["Institution", "Course Title", "Upcoming Date", "Duration", "Training Mode", "Full Fee", "Funded Fee"]

# Extract text and create embeddings for MyCareersFuture
careers_text = extract_text_from_csv(careers_data, careers_text_columns)
careers_chunks = chunk_text(careers_text)
careers_embeddings = create_embeddings(careers_chunks)
careers_faiss_index = build_faiss_index(careers_embeddings)

# Extract text and create embeddings for SkillsFuture
skills_text = extract_text_from_csv(skills_data, skills_text_columns)
skills_chunks = chunk_text(skills_text)
skills_embeddings = create_embeddings(skills_chunks)
skills_faiss_index = build_faiss_index(skills_embeddings)

print("Data processing and FAISS index creation complete.")


# CO-STAR Framework Components
context = """
You are an AI assistant designed to answer questions about job opportunities from MyCareersFuture and courses from SkillsFuture. Your goal is to provide accurate, relevant, and concise answers based on the datasets.

If a question falls outside the domain of jobs or courses, politely decline to answer by using a single sentence as your response. Always maintain a professional and educational tone.
"""

outcome = """1. Your main directive is to provide the top 3 jobs or courses from the datasets that would fit the user's portfolio or requests, please also provide the url link to the top 3 jobs or courses.
2. If the user asks a question about jobs or courses, focus on providing relevant information by extracting context from the datasets.
3. Include useful links where the user can find detailed information about jobs or courses.
4. Conclude with a follow-up question that encourages exploration of related opportunities or courses."""

scale = """Adapt responses based on the complexity of the user's queries. For beginners, provide straightforward answers. For advanced users, include additional insights such as job market trends or course recommendations."""

time = """Keep each response concise and to the point. Provide enough information to answer the user's question but avoid overwhelming them with unnecessary details."""

actor = """You, the AI assistant, act as a guide and advisor. Engage with users by asking follow-up questions, providing clarifications, and offering actionable recommendations."""

resources = """Utilize the MyCareersFuture and SkillsFuture datasets, along with FAISS for retrieval and SentenceTransformer for embeddings."""

def answer_question(query, cv_text, mode, history, model_name=MODEL, chunks=[], link_column="", data=pd.DataFrame()):
    llm = OllamaLLM(model=MODEL)
    MAX_HISTORY_LENGTH = 10

    # Limit conversation history
    if len(history) > MAX_HISTORY_LENGTH:
        history = history[-MAX_HISTORY_LENGTH:]

    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        combined_query = f"{query} Relevant CV context: {cv_text}" if cv_text else query

        if "career" in mode:
            faiss_index = careers_faiss_index
            chunks = careers_chunks
            data = careers_data
            link_column = "Link" 

        elif "skill" in mode:
            faiss_index = skills_faiss_index
            chunks = skills_chunks
            data = skills_data
            link_column = "Link" 

        relevant_chunks = search_faiss_index(
            query=combined_query,
            faiss_index=faiss_index,
            chunks=chunks,
            model=model,
            k=5,  # Retrieve top 5 results
            diversity_threshold=0.8  # Minimum diversity threshold for cosine similarity
        )

        query_embedding = model.encode([query + cv_text], convert_to_tensor=False)
        distances, indices = faiss_index.search(np.array(query_embedding), k=3)
        # Map chunks to original dataset rows
        links = []

        for i in indices[0]:
            if i < len(data):  # Ensure index is within bounds
                row = data.iloc[i]
                # results.append(chunks[i])
                links.append(row.get(link_column, "No link available"))

        # Combine chunks with links
        combined_chunks = "\n".join([f"{chunk}\nLink: {link}" for chunk, link in zip(relevant_chunks, links)])


        # Add context to the prompt
        prompt = (
            context + outcome + scale + time + actor + resources +
            "\nConversation History:\n" +
            "\n".join([f"{sender}: {message}" for sender, message in history]) +
            f"\n\nRelevant Context:\n{combined_chunks}\n\nQuestion: {query}"
        )

        response = llm(prompt)
        history.append(("Chatbot", response))

        return history, response
    except Exception as e:
        return history, f"Error: {str(e)}"


if __name__ == "__main__":
    user_query = "What jobs are available in the IT sector?"
    history = []
    model_name = MODEL

    # Use MyCareersFuture FAISS index
    history, response = answer_question(
        user_query,
        history,
        model_name,
        careers_faiss_index,
        careers_chunks,
        # link_column="Link",
        data=careers_data
    )
    print(response)

    user_query = "What courses are available for data analytics?"
    history, response = answer_question(
        user_query,
        history,
        model_name,
        skills_faiss_index,
        skills_chunks,
        # link_column="Link",
        data=skills_data
    )
    print(response)