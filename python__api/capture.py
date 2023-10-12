import os
import uuid
from fastapi import UploadFile, HTTPException
from models import SessionLocal, CapturedImage
from predict import predict_and_store_predictions  # Import the prediction function from predict.py

upload_directory = "img"

def capture_and_save_image(file: UploadFile):
    try:
        unique_filename = str(uuid.uuid4()) + file.filename
        filename = os.path.join(upload_directory, unique_filename)
        os.makedirs(upload_directory, exist_ok=True)
        with open(filename, "wb") as image_file:
            image_file.write(file.file.read())
        db = SessionLocal()
        db_image = CapturedImage(filename=unique_filename)
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        db.close()

        # Now, call the prediction function from predict.py
        image_id = db_image.id
        image_path = os.path.join(upload_directory, db_image.filename)
        predict_and_store_predictions(image_id, image_path)

        return {"message": "Image captured and saved successfully"}
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail="Image capture error")
