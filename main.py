from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import random
import time

# --- Setup ---
app = FastAPI(title="Veritas Deepfake API")

# Enable CORS so the React frontend can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Vercel URL here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AI Model Logic ---
# In a real app, you would load PyTorch/TensorFlow here.
# Example: model = torch.load("mesonet.pth")

def preprocess_image(image_bytes):
    """Convert bytes to PIL Image and resize for model."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("RGB") # Ensure standard color mode
        image = image.resize((256, 256)) # Standard AI input size
        return image
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image file")

def run_inference(image):
    """
    This is where the actual AI detection happens.
    Currently acts as a placeholder for the real model.
    """
    
    # --- TODO: Insert Real Model Code Here ---
    # tensor = transform(image).unsqueeze(0)
    # prediction = model(tensor)
    # confidence = torch.sigmoid(prediction).item()
    # return confidence
    # -----------------------------------------

    # For demonstration, we simulate detection logic
    # In a real scenario, this would return the model's actual confidence
    time.sleep(1) # Simulate GPU processing time
    
    # Mock Logic: Returns a random confidence for demo
    # (Replace this with real model output)
    simulated_confidence = random.uniform(0.1, 0.99)
    return simulated_confidence

# --- API Endpoints ---

@app.get("/")
def home():
    return {"status": "online", "message": "Deepfake Detection API Ready"}

@app.post("/detect")
async def detect_deepfake(file: UploadFile = File(...)):
    """
    Main endpoint to handle image upload and detection.
    """
    # 1. Read Image
    image_data = await file.read()
    
    # 2. Preprocess
    image = preprocess_image(image_data)
    
    # 3. Run AI Model
    confidence_score = run_inference(image)
    
    # 4. Interpret Results
    # Usually, if score > 0.5, it's considered Fake (or Real, depending on training)
    # Let's assume 1.0 = Fake, 0.0 = Real
    is_fake = confidence_score > 0.5
    
    return {
        "filename": file.filename,
        "is_fake": is_fake,
        "confidence": confidence_score,
        "processing_time": 1.2, # seconds
        "model_version": "v2.1-beta"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)