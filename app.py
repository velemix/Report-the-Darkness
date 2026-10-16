from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
DB_FILE = "complaints.json"

def save_to_file(complaint, result, location="Not provided"):
    data = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
                
    data.append({
        "complaint": complaint,
        "ai_result": result,
        "location": location
    })
    
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
@app.route('/view-complaints')
def view_complaints():
    data = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    return render_template('view_complaints.html', complaints=data)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/send-report/<int:index>", methods=["POST"])
def send_report(index):
    data = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
                
    if 0 <= index < len(data):
        item = data[index]
        
        # Configure your sender email and receiver barangay email
        sender_email = os.environ.get("MAIL_USERNAME", "your_email@gmail.com")
        sender_password = os.environ.get("MAIL_PASSWORD", "your_app_password")
        receiver_email = "yoomysigmaguy@gmail.com" # Replace with actual barangay email
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"Barangay Complaint Report: {item.get('complaint', 'Issue')[:30]}"
        
        body = f"""
        Good day Barangay Official,
        
        A new community complaint has been logged through the reporting portal:
        
        - Complaint / Issue: {item.get('complaint')}
        - Location Coordinates: {item.get('location', 'Not provided')}
        - AI Analysis & Suggested Action:
        {item.get('ai_result')}
        
        Please review and action accordingly. Thank you!
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            return jsonify({"status": "success", "message": "Report emailed successfully!"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
            
    return jsonify({"status": "error", "message": "Complaint not found"}), 404

@app.route("/complaint", methods=["POST"])
def classify_complaint():
    lat = request.form.get("latitude")
    lng = request.form.get("longitude")
    
    if not lat and request.is_json:
        req_data = request.json or {}
        lat = req_data.get("latitude")
        lng = req_data.get("longitude")
        
    location_str = f"{lat}, {lng}" if lat and lng and lat != "Unknown" else "Location not shared"

    # 1. Handle Audio Files
    if 'audio' in request.files:
        audio_file = request.files['audio']
        audio_bytes = audio_file.read()
        
        if not audio_bytes:
            return jsonify({"result": "Audio recording is empty!"}), 400
            
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[
                    "Listen to this barangay complaint voice recording, transcribe it, and classify it.",
                    types.Part.from_bytes(data=audio_bytes, mime_type='audio/webm')
                ],
                config=types.GenerateContentConfig(
                    system_instruction="Provide the transcription of the audio followed by:\nCategory:\nPriority:\nSuggested action:"
                )
            )
            ai_output = response.text
            save_to_file("[Voice Recording]", ai_output, location=location_str)
            return jsonify({"result": ai_output})
            
        except Exception as e:
            print(f"Audio processing error details: {e}")
            return jsonify({"result": f"Error processing audio: {str(e)}"}), 500

    if 'file' in request.files:
        text_file = request.files['file']
        complaint_text = text_file.read().decode('utf-8')
    else:
        complaint_text = request.form.get("complaint", "")

    if not complaint_text:
        return jsonify({"result": "Complaint cannot be empty!"}), 400

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
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
        save_to_file(complaint_text, ai_output, location=location_str)
        return jsonify({"result": ai_output})
        
    except Exception as e:
        print(f"Text processing error details: {e}")
        return jsonify({"result": f"Error processing text: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)