from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import time

app = Flask(__name__)

# 1. ENABLE CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# 2. CONFIGURATION
# We use the working model we found earlier
API_URL = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online", 
        "message": "Veritas AI Backend (Flask) is Running with Real AI"
    })

@app.route('/detect', methods=['POST'])
def detect():
    try:
        # --- 1. Get Token from Render Environment ---
        hf_token = os.environ.get("HF_TOKEN")
        
        if not hf_token:
            print("CRITICAL ERROR: HF_TOKEN is missing!")
            return jsonify({
                "confidence": 0.0, 
                "label": "Config Error", 
                "message": "Server Token Missing"
            }), 500

        headers = {"Authorization": f"Bearer {hf_token}"}
        
        # --- 2. Check File ---
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Read file bytes
        image_data = file.read()
        print(f"Sending image to AI Model: {API_URL}")

        # --- 3. Send to Hugging Face ---
        response = requests.post(API_URL, headers=headers, data=image_data)
        
        # Handle "Model Loading" (Error 503)
        if response.status_code == 503:
            print("Model is loading... waiting 10 seconds...")
            time.sleep(10)
            response = requests.post(API_URL, headers=headers, data=image_data)

        # Handle Errors
        if response.status_code != 200:
            print(f"AI API Error: {response.status_code} - {response.text}")
            return jsonify({
                "confidence": 0.0, 
                "label": "API Error", 
                "message": f"Status {response.status_code}"
            }), 200 # Return 200 so frontend handles it gracefully

        # --- 4. Robust Parsing Logic ---
        result = response.json()
        print(f"AI Raw Result: {result}")

        # Fix nested lists [[...]]
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            result = result[0]

        fake_score = 0.0
        real_score = 0.0
        
        if isinstance(result, list):
            for item in result:
                label_raw = str(item.get('label', ''))
                label = label_raw.lower()
                score = float(item.get('score', 0.0))
                
                # Check for "Fake" labels
                if label in ['fake', 'ai', 'artificial', 'deepfake', 'label_1', '1']:
                    fake_score = max(fake_score, score)
                # Check for "Real" labels
                elif label in ['real', 'authentic', 'original', 'human', 'label_0', '0']:
                    real_score = max(real_score, score)

        # Fallback Logic
        if fake_score == 0.0 and real_score == 0.0 and len(result) > 0:
            top_item = max(result, key=lambda x: x.get('score', 0))
            if top_item.get('label') == 'artificial':
                fake_score = top_item.get('score')
            else:
                real_score = top_item.get('score')

        # Verdict
        is_fake = fake_score > real_score
        confidence = fake_score if is_fake else real_score
        label = "AI" if is_fake else "Real"

        # Return JSON
        response_data = {
            "is_fake": is_fake,
            "confidence": confidence,
            "label": label,
            "fake_score": fake_score,
            "real_score": real_score,
            "message": "Analysis successful"
        }
        
        print(f"Sending response: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        print(f"Error processing image: {e}")
        return jsonify({"error": str(e), "confidence": 0.0, "label": "Error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)