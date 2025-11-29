from fastapi import FastAPI, UploadFile, File, HTTPException
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

# --- SECURITY NOTE ---
# Ensure this token is valid! 
# If this token is invalid/expired, the API returns 401 and you get 0.0% confidence.
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
        
        # --- Handle "Model Loading" (503) ---
        if response.status_code == 503:
            error_data = response.json()
            estimated_time = error_data.get("estimated_time", 10)
            print(f"Model is loading... waiting {estimated_time} seconds")
            time.sleep(estimated_time)
            response = requests.post(API_URL, headers=headers, data=image_data)

        # --- Handle API Errors (400, 401, 500) ---
        if response.status_code != 200:
            print(f"CRITICAL AI ERROR: {response.status_code} - {response.text}")
            # Return a special error format the frontend might display
            return {
                "is_fake": False,
                "confidence": 0.0, 
                "label": "API Error",
                "message": f"HuggingFace Error: {response.status_code}"
            }

        result = response.json()
        print(f"AI Raw Result: {result}") # <--- CHECK RENDER LOGS FOR THIS LINE

        # --- ROBUST PARSING LOGIC ---
        
        # Handle [[{...}]] structure (List of lists)
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            result = result[0]

        fake_score = 0.0
        real_score = 0.0
        
        if isinstance(result, list):
            for item in result:
                # Normalize label to lowercase
                label = str(item.get('label', '')).lower()
                score = float(item.get('score', 0.0))
                
                # CHECK 1: Standard Labels
                if label in ['fake', 'ai', 'artificial', 'deepfake']:
                    fake_score = score
                elif label in ['real', 'authentic', 'original']:
                    real_score = score
                
                # CHECK 2: Technical Labels (LABEL_0 / LABEL_1)
                # Note: You must verify which is which for your specific model.
                # Usually LABEL_1 = Fake, LABEL_0 = Real for this specific model, 
                # but sometimes it is swapped. We assume 1=Fake, 0=Real here.
                elif label == 'label_1': 
                    fake_score = score
                elif label == 'label_0': 
                    real_score = score

        # If we failed to find ANY scores, it means the labels didn't match anything we know
        if fake_score == 0.0 and real_score == 0.0:
            print(f"WARNING: No matching labels found in {result}")
            # Fallback: Assume the highest score is the prediction, even if we don't know the label
            if len(result) > 0:
                top_item = max(result, key=lambda x: x.get('score', 0))
                return {
                    "is_fake": False,
                    "confidence": top_item.get('score', 0.0),
                    "label": f"Unknown Label: {top_item.get('label')}",
                    "message": "Labels did not match known Real/Fake list"
                }

        # Determine verdict
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
        print(f"CRITICAL SERVER ERROR: {e}")
        return {
            "is_fake": False,
            "confidence": 0.0, 
            "label": "Server Error", 
            "message": str(e)
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)