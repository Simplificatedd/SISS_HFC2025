from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from CV_parser import CvConverter
import logging
from main import answer_question
from config import MODEL
from flask_cors import CORS
from main import load_csv_data
from langchain_ollama import OllamaLLM


app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Store cv_text to persist across requests
cv_text_cache = ""


CAREERS_CSV_PATH = "dataset/mycareersfuture_jobs.csv"
SKILLS_CSV_PATH = "dataset/skillsfuture_courses.csv"

# Load datasets
careers_data = load_csv_data(CAREERS_CSV_PATH)
skills_data = load_csv_data(SKILLS_CSV_PATH)


@app.route("/api/chat", methods=["POST"])
def chat():
    global cv_text_cache
    try:
        # Retrieve form data
        message = request.form.get("message", "")
        mode = request.form.get("mode", "")
        uploaded_file = request.files.get("uploadedFile")
        history = request.form.get("history", "[]")
        
        # Convert history from string to Python list
        history = eval(history)

        if "remove resume" in message:
            cv_text_cache = ""  # Clear the cached CV text
            return jsonify({"response": "Your resume has been removed.", "status": "success"}), 200


        # Check if a resume is uploaded
        if uploaded_file:
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)

            try:
                # Process the uploaded resume
                converter = CvConverter(filepath)
                cv_text_cache = converter.convert_to_text()
                # print(f"Extracted CV Text: {cv_text_cache}")
            except Exception as e:
                logging.error(f"Error processing CV: {e}")
                return jsonify({"response": "Error processing CV.", "status": "error"}), 500

        # Use empty string if no resume is uploaded
        cv_text = cv_text_cache if cv_text_cache.strip() else ""

        # Generate a response using the LLM
        history, response = answer_question(
            query=message,
            cv_text=cv_text,  # Use the CV text or an empty string
            mode=mode,
            history=history,
        )

        return jsonify({
            "response": response["text"],
            "recommendations": response["recommendations"],
            "status": "success"
        })

    except Exception as e:
        # Log the error and send an appropriate message
        logging.error(f"Error in /api/chat endpoint: {e}")
        return jsonify({"response": "An error occurred while processing your request. Please try again later.", "status": "error"}), 500



@app.route("/api/details", methods=["POST"])
def details():
    try:
        title = request.json.get("title")
        mode = request.json.get("mode", "career")
        data = careers_data if mode == "career" else skills_data

        # Match the title column based on mode
        title_column = "Job Title" if mode == "career" else "Course Title"
        details = data[data[title_column] == title].to_dict(orient="records")
        if not details:
            return jsonify({"status": "error", "details": "No additional details found."})

        return jsonify({"status": "success", "details": details[0]})

    except Exception as e:
        return jsonify({"status": "error", "details": str(e)})

@app.route("/api/paraphrase", methods=["POST"])
def paraphrase():
    try:
        text = request.json.get("text", "").strip()
        if not text:
            return jsonify({"status": "error", "text": "No text provided to process."}), 400

        # Initialize the LLM for summarization
        llm = OllamaLLM(model=MODEL)

        # Call LLM to paraphrase/summarize the text
        paraphrased_text = llm(
            f"""
            You are a professional assistant. Summarize the following content succinctly and clearly in a friendly and direct manner.
            Avoid any greeting phrases like "hey there, sure thing."
            If you get information about "Location: ", it means where this job is located at.
            Focus on delivering the core information without explaining the summarization process.
            Always end off by asking the user a question if they need help with other things.

            Content to Summarize:
            {text}
            """
        ).strip()

        if not paraphrased_text:
            raise ValueError("LLM returned empty text.")

        return jsonify({"status": "success", "text": paraphrased_text})

    except Exception as e:
        logging.error(f"Error in /api/paraphrase: {e}")
        return jsonify({"status": "error", "text": "An error occurred while processing the text."}), 500


if __name__ == "__main__":
    app.run(debug=False)
