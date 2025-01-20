from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from CV_parser import CvConverter
import logging
from main import answer_question
from config import MODEL
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Store cv_text to persist across requests
cv_text_cache = ""

@app.route("/api/chat", methods=["POST"])
def chat():
    global cv_text_cache  # Use a global variable to persist the CV text
    try:
        message = request.form.get("message", "")
        mode = request.form.get("mode", "")
        uploaded_file = request.files.get("uploadedFile")
        history = request.form.get("history", "[]")

        history = eval(history)  # Convert history string back to list

        if uploaded_file:
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)

            try:
                converter = CvConverter(filepath)
                cv_text_cache = converter.convert_to_text()  # Save the parsed CV text to the cache
                print(f"Extracted CV Text: {cv_text_cache}")  # Debug log for extracted text
            except Exception as e:
                logging.error(f"Error processing CV: {e}")
                return jsonify({"response": "Error processing CV.", "status": "error"}), 500

        if not cv_text_cache.strip():  # Check if cv_text_cache is still empty
            return jsonify({"response": "Resume processing failed. Please try uploading a valid PDF.", "status": "error"}), 400

        # Get the response
        history, response = answer_question(
            query=message,
            cv_text=cv_text_cache,  # Pass the extracted CV text
            mode=mode,
            history=history,
        )

        return jsonify({"response": response, "status": "success"})

    except Exception as e:
        logging.error(f"Error in /api/chat endpoint: {e}")
        return jsonify({"response": f"Error: {str(e)}", "status": "error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
