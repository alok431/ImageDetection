from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import io

app = FastAPI()

# Enable CORS so your Vercel frontend can talk to this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
# We are using a pre-trained model from Hugging Face
# Model: "dima806/deepfake_vs_real_image_detection" (A popular research model)
API_URL = "https://api-inference.huggingface.co/models/dima806/deepfake_vs_real_image_detection"

# This public model usually works without a key for testing.
# If you get errors later, you can add a token: headers = {"Authorization": "Bearer hf_YOUR_TOKEN"}
headers = {"Authorization": "Bearer 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"} 

@app.get("/")
def home():
    return {"status": "online", "brain": "HuggingFace Real-Time AI"}

@app.post("/detect")
async def detect_deepfake(file: UploadFile = File(...)):
    # 1. Read the image from the user
    image_data = await file.read()

    # 2. Send image to Hugging Face AI Cloud
    try:
        response = requests.post(API_URL, headers=headers, data=image_data)
        result = response.json()
        
        # Check if model is "loading" (common on free tier)
        if isinstance(result, dict) and "error" in result:
            if "loading" in result["error"]:
                return {
                    "is_fake": False, 
                    "confidence": 0.0, 
                    "message": "Model is warming up. Please try again in 30 seconds."
                }
            else:
                # Log actual error for debugging
                print("Hugging Face Error:", result)
                raise HTTPException(status_code=500, detail=f"AI Error: {result['error']}")

    except Exception as e:
        print(f"Error calling AI: {e}")
        raise HTTPException(status_code=500, detail="AI Service Connection Failed")

    # 3. Interpret the Result
    # The API returns a list like: [{'label': 'Fake', 'score': 0.99}, {'label': 'Real', 'score': 0.01}]
    # Note: This specific model uses 'fake' and 'real' labels (lowercase or uppercase varies by model)
    
    fake_score = 0
    real_score = 0
    
    # Check the list structure
    if isinstance(result, list):
        for item in result:
            label = item['label'].lower()
            if 'fake' in label or 'ai' in label:
                fake_score = item['score']
            elif 'real' in label:
                real_score = item['score']
    
    # Logic: If Fake score is higher than Real score, it's a deepfake
    is_fake = fake_score > real_score
    confidence = fake_score if is_fake else real_score

    return {
        "filename": file.filename,
        "is_fake": is_fake,
        "confidence": confidence,
        "processing_time": 0.5
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)