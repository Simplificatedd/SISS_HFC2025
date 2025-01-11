from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path
from langchain_ollama.llms import OllamaLLM
from langchain_ollama import OllamaEmbeddings
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS

from docling.document_converter import DocumentConverter

from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import ollama
import os
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path

CAREERS_FILEPATH = Path('dataset/mycareersfuture_jobs.csv')
SKILLS_FILEPATH = Path('dataset/skillsfuture_courses.csv')

# Load environment variables from a .env file
load_dotenv()

llm = OllamaLLM(model="llama3.2")

careers_loader = CSVLoader(file_path=CAREERS_FILEPATH)
skills_loader = CSVLoader(file_path=SKILLS_FILEPATH)

careers_docs = careers_loader.load_and_split()
skills_docs = skills_loader.load_and_split()

vector_store_careers.add_documents(documents=careers_docs)
vector_store_skills.add_documents(documents=skills_docs)

retriever = vector_store.as_retriever()

# Set up system prompt
system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise."
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
    
])

# Create the question-answer chain
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)