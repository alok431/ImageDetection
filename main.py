from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import time

app = Flask(__name__)

# 1. CORS Setup
CORS(app, resources={r"/*": {"origins": "*"}})

# --- BULLETPROOF CONFIGURATION (UPDATED MODELS) ---
# We list multiple models. If one fails, the code automatically tries the next.
AI_MODELS = [
      # 1. PrithivML's DeepFake Detector (Very Popular)
    "https://api-inference.huggingface.co/models/prithivMLmods/Deep-Fake-Detector-v2-Model",
    
    # 2. Naman's Detector (Backup)
    "https://api-inference.huggingface.co/models/Naman712/Deep-fake-detection",
    
    # 3. Umm-Maybe (Might be down, but keep as fallback)
    "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector",
    
    # 4. FaceFake (Another alternative)
    "https://api-inference.huggingface.co/models/facefake/deepfake_detection_v2"
]

def parse_result(result):
    """Helper function to unify labels from different models"""
    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
        result = result[0]

    fake_score = 0.0
    real_score = 0.0
    
    if isinstance(result, list):
        for item in result:
            label = str(item.get('label', '')).lower()
            score = float(item.get('score', 0.0))
            
            if label in ['fake', 'ai', 'artificial', 'deepfake', 'label_1', '1', 'deepfake']:
                fake_score = max(fake_score, score)
            elif label in ['real', 'authentic', 'original', 'human', 'label_0', '0', 'realism']:
                real_score = max(real_score, score)

    # Fallback
    if fake_score == 0.0 and real_score == 0.0 and len(result) > 0:
        top = result[0]
        if 'fake' in top.get('label', '').lower() or 'artificial' in top.get('label', '').lower():
            fake_score = top.get('score')
        else:
            real_score = top.get('score')

    is_fake = fake_score > real_score
    confidence = fake_score if is_fake else real_score
    label = "AI" if is_fake else "Real"

    return {
        "is_fake": is_fake,
        "confidence": confidence,
        "label": label,
        "fake_score": fake_score,
        "real_score": real_score
    }

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "online", "message": "Backend running with Multi-Model Failover v2"})

@app.route('/detect', methods=['POST'])
def detect():
    try:
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            return jsonify({"confidence": 0, "label": "Config Error", "message": "Token Missing"}), 500
        
        headers = {"Authorization": f"Bearer {hf_token}"}
        
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        file = request.files['file']
        image_data = file.read()
        
        last_error = ""
        model_tried_count = 0
        
        # --- LOOP THROUGH MODELS ---
        for model_url in AI_MODELS:
            model_tried_count += 1
            try:
                print(f"Trying Model {model_tried_count}: {model_url}...")
                response = requests.post(model_url, headers=headers, data=image_data)
                
                if response.status_code == 503:
                    time.sleep(5)
                    response = requests.post(model_url, headers=headers, data=image_data)

                if response.status_code == 200:
                    print(f"SUCCESS with {model_url}")
                    result = response.json()
                    response_data = parse_result(result)
                    response_data["model_used"] = model_url  # Debug info
                    return jsonify(response_data)
                
                print(f"Failed {model_url}: Status {response.status_code}")
                last_error = f"Status {response.status_code}"
                
            except Exception as e:
                print(f"Exception with {model_url}: {e}")
                last_error = str(e)
                continue

        # If ALL models fail
        return jsonify({
            "is_fake": False,
            "confidence": 0.0,
            "label": "All Models Failed",
            "message": f"Could not connect to any AI. Tried {model_tried_count} models. Last error: {last_error}"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e), "confidence": 0.0, "label": "Error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)