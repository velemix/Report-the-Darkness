from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
from google.genai.errors import ServerError
import json
import os

app = Flask(__name__)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
DB_FILE = "complaints.json"

def save_to_file(complaint, result):
    data = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    data.append({"complaint": complaint, "ai_result": result})
    
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
@app.route('/view-complaints')
def view_complaints():
    try:
        with open('complaints.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return {"error": "No complaints file found yet."}, 404

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/complaint", methods=["POST"])
def classify_complaint():
    if 'audio' in request.files:
        audio_file = request.files['audio']
        audio_bytes = audio_file.read()
        
        if not audio_bytes:
            return jsonify({"result": "Audio recording is empty!"}), 400
            
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[
                    "Listen to this barangay complaint voice recording, transcribe it, and classify it.",
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type='audio/webm', 
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction="Provide the transcription of the audio followed by:\nCategory:\nPriority:\nSuggested action:"
                )
            )
            ai_output = response.text
            save_to_file("[Voice Recording]", ai_output)
            return jsonify({"result": ai_output})
            
        except ServerError:
            return jsonify({
                "result": "The AI server is experiencing high traffic right now. Please wait a few seconds and try submitting again."
            }), 503

    data = request.json or {}
    complaint_text = data.get("complaint", "")
    if not complaint_text:
        return jsonify({"result": "Complaint cannot be empty!"}), 400

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=f"""
Classify this barangay complaint.

Complaint:
{complaint_text}

Respond with:
Category:
Priority:
Suggested action:
"""
        )
        ai_output = response.text
        save_to_file(complaint_text, ai_output)
        return jsonify({"result": response.text})
        
    except ServerError:
        return jsonify({
            "result": "The AI server is experiencing high traffic right now. Please wait a few seconds and try submitting again."
        }), 503

if __name__ == "__main__":
    app.run(debug=True)