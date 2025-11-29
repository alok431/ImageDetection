from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import uvicorn
import time

app = FastAPI()

# 1. CORS Setup
# This allows your Vercel frontend to verify the backend is safe to talk to.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# 2. Configuration
# We use a reliable deepfake detection model from Hugging Face
API_URL = "https://api-inference.huggingface.co/models/dima806/deepfake_vs_real_image_detection"

# WARNING: In production, store this in an Environment Variable!
headers = {"Authorization": "Bearer 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"}

@app.get("/")
def home():
    return {"status": "online", "message": "FastAPI Backend is Running"}

@app.post("/detect")
async def detect_deepfake(file: UploadFile = File(...)):
    try:
        print(f"--- Processing Image: {file.filename} ---")
        
        # Read the file bytes
        image_data = await file.read()

        # Send to Hugging Face
        response = requests.post(API_URL, headers=headers, data=image_data)
        
        # --- Handle "Model Loading" Error ---
        # Hugging Face serverless models go to sleep. If it's waking up, it returns a 503 error.
        if response.status_code == 503:
            error_data = response.json()
            estimated_time = error_data.get("estimated_time", 10)
            print(f"Model is loading... waiting {estimated_time} seconds")
            time.sleep(estimated_time) # Wait for model to load
            # Retry once
            response = requests.post(API_URL, headers=headers, data=image_data)

        # Check for errors again after retry
        if response.status_code != 200:
            print(f"AI Error: {response.text}")
            return {
                "confidence": 0.0, 
                "label": "Error",
                "message": f"AI Error: {response.status_code}"
            }

        result = response.json()
        print(f"AI Raw Result: {result}")

        # --- PARSING LOGIC ---
        # The AI returns a list: [{'label': 'real', 'score': 0.6}, {'label': 'fake', 'score': 0.4}]
        
        fake_score = 0.0
        real_score = 0.0
        
        # Handle case where result is wrapped in an extra list [[...]]
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            result = result[0]

        # Extract scores
        if isinstance(result, list):
            for item in result:
                label = str(item.get('label', '')).lower()
                score = float(item.get('score', 0.0))
                
                if label in ['fake', 'ai', 'artificial', 'deepfake']:
                    fake_score = score
                elif label in ['real', 'authentic', 'original']:
                    real_score = score
        
        # Determine final verdict
        is_fake = fake_score > real_score
        confidence = fake_score if is_fake else real_score
        label = "AI" if is_fake else "Real"

        # Return format expected by your Frontend
        return {
            "is_fake": is_fake,
            "confidence": confidence,
            "label": label,
            "fake_score": fake_score,
            "real_score": real_score
        }

    except Exception as e:
        print(f"CRITICAL SERVER ERROR: {e}")
        return {
            "confidence": 0.0, 
            "label": "Error", 
            "message": str(e)
        }

if __name__ == "__main__":
    # Render requires the app to run on port 10000 (or the $PORT env var)
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)