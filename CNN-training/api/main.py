from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
from io import BytesIO
from PIL import Image
import tensorflow as tf

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL = tf.keras.models.load_model("../saved-models/model.keras", compile=False)
autoencoder = tf.keras.models.load_model('../saved-models/autoencoder_model.h5')
threshold=0.19881732761859894  #got this from the autoencoder we trained
CLASS_NAMES = ['Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy']

@app.get("/ping")
async def ping():
    return "Hello, I am alive"

def read_file_as_image(data) -> np.ndarray:
    image = Image.open(BytesIO(data)).convert('RGB')  
    image = image.resize((256, 256))  # Resize image
    image = np.array(image) / 255.0  # Rescale image
    return image
RECONSTRUCTION_THRESHOLD=0.19881732761859894
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image = read_file_as_image(await file.read())
    img_batch = np.expand_dims(image, 0) 
    reconstructed_image = autoencoder.predict(img_batch)

    # Compute reconstruction error
    reconstruction_error = np.mean(np.abs(reconstructed_image - img_batch), axis=(1, 2, 3))[0] 

    if reconstruction_error > RECONSTRUCTION_THRESHOLD:
        return {
            'message': "I can not classify this image",
            'reconstruction_error': reconstruction_error
        }

    predictions = MODEL.predict(img_batch)

    predicted_class = CLASS_NAMES[np.argmax(predictions[0])]
    confidence = float(np.max(predictions[0]))

      
    return {
        'class': predicted_class,
        'confidence': confidence
    }

if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8000)