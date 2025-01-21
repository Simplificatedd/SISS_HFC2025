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
        message = request.form.get("message", "")
        mode = request.form.get("mode", "")
        uploaded_file = request.files.get("uploadedFile")
        history = request.form.get("history", "[]")

        history = eval(history)

        if uploaded_file:
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)

            try:
                converter = CvConverter(filepath)
                cv_text_cache = converter.convert_to_text()
                print(f"Extracted CV Text: {cv_text_cache}")
            except Exception as e:
                logging.error(f"Error processing CV: {e}")
                return jsonify({"response": "Error processing CV.", "status": "error"}), 500

        if not cv_text_cache.strip():
            return jsonify({"response": "Resume processing failed. Please try uploading a valid PDF.", "status": "error"}), 400

        # Get the response
        history, response = answer_question(
            query=message,
            cv_text=cv_text_cache,
            mode=mode,
            history=history,
        )

        return jsonify({
            "response": response["text"],
            "recommendations": response["recommendations"],
            "status": "success"
        })

    except Exception as e:
        logging.error(f"Error in /api/chat endpoint: {e}")
        return jsonify({"response": f"Error: {str(e)}", "status": "error"}), 500



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
        text = request.json.get("text", "")
        if not text.strip():
            return jsonify({"status": "error", "text": "No text provided to process."}), 400

        llm = OllamaLLM(model=MODEL)
        paraphrased_text = llm(
            f"""
            You are a professional career assistant chatbot. Respond in a concise, conversational, and user-friendly tone.
            Summarize the following information in a way that feels natural and engaging. Do not reveal to the user that you are summarizing or processing the data.
            Avoid overly formal language; respond as if you're directly answering the user's question with clarity.

            Original Information:
            {text}

            Your Response:
            """
        )
        return jsonify({"status": "success", "text": paraphrased_text})
    except Exception as e:
        logging.error(f"Error in /api/paraphrase: {e}")
        return jsonify({"status": "error", "text": "Failed to process text."}), 500




if __name__ == "__main__":
    app.run(debug=True)
