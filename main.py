from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import uvicorn
import time

app = FastAPI()

# 1. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Configuration
API_URL = "https://api-inference.huggingface.co/models/dima806/deepfake_vs_real_image_detection"

@app.get("/")
def home():
    return {"status": "online", "message": "Backend is running with Universal Parser"}

@app.post("/detect")
async def detect_deepfake(file: UploadFile = File(...)):
    try:
        # --- DEBUG: Verify Token Loading ---
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            print("CRITICAL ERROR: HF_TOKEN is missing!")
            return {"is_fake": False, "confidence": 0.0, "label": "Config Error", "message": "Token Missing"}
        
        # Log first 4 chars to prove it's loaded (safe to show in logs)
        print(f"Token loaded: {hf_token[:4]}********") 

        headers = {"Authorization": f"Bearer {hf_token}"}
        
        image_data = await file.read()
        print(f"Sending image to AI... ({len(image_data)} bytes)")

        response = requests.post(API_URL, headers=headers, data=image_data)
        
        # --- Handle Loading/Errors ---
        if response.status_code == 503:
            print("Model loading... retrying in 5s...")
            time.sleep(5)
            response = requests.post(API_URL, headers=headers, data=image_data)

        if response.status_code != 200:
            print(f"AI API Error: {response.status_code} - {response.text}")
            return {
                "is_fake": False, 
                "confidence": 0.0, 
                "label": "API Error", 
                "message": f"Status {response.status_code}"
            }

        # --- UNIVERSAL PARSING LOGIC ---
        result = response.json()
        print(f"AI Raw Result: {result}") # Check Render Logs for this line!

        # Unwrap list-in-list
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            result = result[0]

        fake_score = 0.0
        real_score = 0.0
        
        # Try to parse standard labels
        if isinstance(result, list):
            for item in result:
                label_raw = str(item.get('label', ''))
                label = label_raw.lower()
                score = float(item.get('score', 0.0))
                
                # Check 1: Explicit Fake Labels
                if label in ['fake', 'ai', 'artificial', 'deepfake', 'label_1', '1']:
                    fake_score = max(fake_score, score)
                # Check 2: Explicit Real Labels
                elif label in ['real', 'authentic', 'original', 'label_0', '0']:
                    real_score = max(real_score, score)
                # Check 3: Partial Matches (e.g. "Fake Image")
                elif "fake" in label:
                    fake_score = max(fake_score, score)
                elif "real" in label:
                    real_score = max(real_score, score)

        # --- FALLBACK: If standard parsing failed (both 0), force a result ---
        if fake_score == 0.0 and real_score == 0.0 and len(result) > 0:
            print("Warning: Labels not recognized. Using Fallback.")
            # Assume the highest score is the answer, default to 'Fake' if we can't tell
            top_item = max(result, key=lambda x: x.get('score', 0))
            fallback_score = top_item.get('score', 0.0)
            fallback_label = str(top_item.get('label', 'Unknown'))
            
            # Return raw result
            return {
                "is_fake": False, # Default to safe
                "confidence": fallback_score,
                "label": fallback_label,
                "message": "Fallback Mode"
            }

        # Calculate final verdict
        is_fake = fake_score > real_score
        confidence = fake_score if is_fake else real_score
        label = "AI" if is_fake else "Real"

        print(f"Verdict: {label} ({confidence*100:.2f}%)")

        return {
            "is_fake": is_fake,
            "confidence": confidence,
            "label": label,
            "fake_score": fake_score,
            "real_score": real_score
        }

    except Exception as e:
        print(f"Server Exception: {e}")
        return {
            "is_fake": False, 
            "confidence": 0.0, 
            "label": "Server Error", 
            "message": str(e)
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)