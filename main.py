from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
MODELS = [
    "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector",
    "https://api-inference.huggingface.co/models/prithivMLmods/Deep-Fake-Detector-Model"
]

# SECURE WAY: Read token from the Environment (Render settings)
# This looks for a variable named "HF_TOKEN" on the server.
hf_token = os.environ.get("HF_TOKEN")
headers = {"Authorization": f"Bearer {hf_token}"}

@app.get("/")
def home():
    return {"status": "online", "version": "SECURE_V10"}

@app.post("/detect")
async def detect_deepfake(file: UploadFile = File(...)):
    start_time = time.time()
    image_data = await file.read()
    
    last_error = ""
    
    for model_url in MODELS:
        try:
            print(f"Trying Model: {model_url}...")
            response = requests.post(model_url, headers=headers, data=image_data)
            
            if response.status_code == 503:
                print("Model loading... waiting 2s")
                time.sleep(2)
                response = requests.post(model_url, headers=headers, data=image_data)

            if response.status_code != 200:
                print(f"Model failed: {response.status_code}")
                last_error = f"Status {response.status_code}"
                continue 

            result = response.json()
            
            # Parsing Logic
            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
                result = result[0]

            fake_score = 0.0
            real_score = 0.0
            
            if isinstance(result, list):
                for item in result:
                    label = str(item.get('label', '')).lower()
                    score = float(item.get('score', 0.0))
                    
                    if label in ['fake', 'ai', 'artificial', 'deepfake']:
                        fake_score = score
                    elif label in ['real', 'authentic', 'original', 'human']:
                        real_score = score
            
            is_fake = fake_score > real_score
            confidence = fake_score if is_fake else real_score
            processing_time = round(time.time() - start_time, 2)

            return {
                "is_fake": is_fake,
                "confidence": confidence,
                "processing_time": processing_time
            }

        except Exception as e:
            print(f"Crash on model {model_url}: {e}")
            last_error = str(e)
            continue

    return {
        "is_fake": False, 
        "confidence": 0, 
        "processing_time": 0,
        "message": f"All models failed. Last error: {last_error}"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)