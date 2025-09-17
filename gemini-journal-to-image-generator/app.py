from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import dotenv
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

dotenv.load_dotenv()

# Initialize GenAI client with API key from env
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()
# origins = [
#     "http://localhost:5173",
#     # add other allowed origins if needed, or use ["*"] for all (not recommended in production)
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],  # allow all HTTP methods
#     allow_headers=["*"],  # allow all headers
# )

# Pydantic model for request body
class ImageRequest(BaseModel):
    journal: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/generate")
async def generate_image(request: ImageRequest):
    print(request)
    prompt = (
        "Convert the following journal entry into a vibrant, uplifting image "
        "that symbolizes hope and positivity: " + request.journal
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash-image-preview",
        contents=prompt,
    )

    image_parts = [
        part.inline_data.data
        for part in response.candidates[0].content.parts
        if part.inline_data
    ]

    if not image_parts:
        return {"error": "No image generated"}

    # Convert binary image data to base64 string for JSON transport
    image_bytes = image_parts[0]
    base64_img = base64.b64encode(image_bytes).decode("utf-8")

    return {"image_base64": base64_img}
    

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)

