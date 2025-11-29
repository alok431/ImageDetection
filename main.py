from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import uvicorn
import time

app = FastAPI()

# 1. CORS Setup (Allows Vercel to talk to Render)
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
    return {"status": "online", "message": "Backend is running correctly"}

@app.post("/detect")
async def detect_deepfake(file: UploadFile = File(...)):
    try:
        # --- CRITICAL: Get Token from Render Environment ---
        # This reads the 'HF_TOKEN' you just saved in the Render Dashboard
        hf_token = os.environ.get("HF_TOKEN")
        
        if not hf_token:
            print("ERROR: HF_TOKEN is missing in Render settings!")
            return {
                "is_fake": False, 
                "confidence": 0.0, 
                "label": "Config Error", 
                "message": "Server Config Error: Token Missing"
            }

        headers = {"Authorization": f"Bearer {hf_token}"}
        
        # Read the uploaded image
        image_data = await file.read()

        # Send to Hugging Face AI
        response = requests.post(API_URL, headers=headers, data=image_data)
        
        # --- Handle "Model Loading" (503 Error) ---
        # If the AI is asleep, wait 10 seconds and try again
        if response.status_code == 503:
            print("Model is loading... waiting 10s...")
            time.sleep(10)
            response = requests.post(API_URL, headers=headers, data=image_data)

        # --- Handle "Unauthorized" (401 Error) ---
        if response.status_code == 401:
            print("Error 401: The Token in Render is invalid or expired.")
            return {
                "is_fake": False, 
                "confidence": 0.0, 
                "label": "Auth Error", 
                "message": "Invalid API Token"
            }

        # Check for other errors
        if response.status_code != 200:
            print(f"AI Error: {response.text}")
            return {
                "is_fake": False, 
                "confidence": 0.0, 
                "label": "AI Error", 
                "message": f"Status {response.status_code}"
            }

        # --- Parse the Success Result ---
        result = response.json()
        print(f"AI Raw Result: {result}")

        # Fix structure if it's a list inside a list [[...]]
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            result = result[0]

        fake_score = 0.0
        real_score = 0.0
        
        # Extract scores from the AI response
        if isinstance(result, list):
            for item in result:
                label = str(item.get('label', '')).lower()
                score = float(item.get('score', 0.0))
                
                if label in ['fake', 'ai', 'artificial', 'deepfake', 'label_1']:
                    fake_score = score
                elif label in ['real', 'authentic', 'original', 'label_0']:
                    real_score = score

        # Decide if it's Fake or Real
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

    except Exception as e:
        print(f"Server Exception: {e}")
        return {
            "is_fake": False, 
            "confidence": 0.0, 
            "label": "Server Error", 
            "message": str(e)
        }

if __name__ == "__main__":
    # Render sets the PORT environment variable automatically
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)