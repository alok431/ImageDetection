from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

# 1. CORS Setup (Allows your Vercel frontend to talk to this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Configuration
# We use a faster model to avoid timeouts
API_URL = "https://api-inference.huggingface.co/models/dima806/deepfake_vs_real_image_detection"

# Your Actual Token (Do not share this publicly in real apps)
headers = {"Authorization": "Bearer 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"}

@app.get("/")
def home():
    return {"status": "online", "version": "DEBUG_MODE_V2"}

@app.post("/detect")
async def detect_deepfake(file: UploadFile = File(...)):
    try:
        print("--- Received Image ---")
        image_data = await file.read()

        # Send to Hugging Face
        print(f"Sending to AI URL: {API_URL}")
        response = requests.post(API_URL, headers=headers, data=image_data)
        
        # --- DEBUG LOGGING ---
        # This prints to Render logs so we can see what happened
        print(f"AI Status Code: {response.status_code}")
        print(f"AI Raw Response: {response.text}") 
        # ---------------------

        if response.status_code != 200:
            # If AI fails, tell the frontend why
            return {
                "is_fake": False, 
                "confidence": 0, 
                "message": f"AI Error: {response.status_code} - {response.text[:100]}..."
            }

        result = response.json()

        # Logic to find Fake/Real score from the AI's answer
        fake_score = 0.0
        real_score = 0.0
        
        # The AI returns a list like: [{'label': 'real', 'score': 0.9}, {'label': 'fake', 'score': 0.1}]
        # ...
        # --- ROBUST PARSING LOGIC ---
        # Handle case where result is a list inside a list: [[...]]
        # ...
        # --- ROBUST PARSING LOGIC ---
        # Handle case where result is a list inside a list: [[...]]
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            result = result[0]

        fake_score = 0.0
        real_score = 0.0
        
        # Iterate through labels safely
        if isinstance(result, list):
            for item in result:
                label = str(item.get('label', '')).lower()
                score = float(item.get('score', 0.0))
                
                # Check for various label names used by different models
                if label in ['fake', 'ai', 'artificial', 'deepfake']:
                    fake_score = score
                elif label in ['real', 'authentic', 'original']:
                    real_score = score
        # ...
        
        is_fake = fake_score > real_score
        confidence = fake_score if is_fake else real_score

        return {
            "is_fake": is_fake,
            "confidence": confidence,
            "processing_time": 0.5
        }

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return {"is_fake": False, "confidence": 0, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Render needs this specific port configuration
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)