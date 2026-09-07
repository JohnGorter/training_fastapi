from fastapi import FastAPI, Form, HTTPException, UploadFile, status, BackgroundTasks
from typing import Annotated
from mymail import sendEmail
from utils import start_external_process, process_file_in_background

app = FastAPI()

@app.post("/image")
async def processImage(image: Annotated[UploadFile, Form()], backgroundtasks:BackgroundTasks):
    if (image.content_type not in ["image/jpeg", "image/png"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image type")
    if (image.size is None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image size not provided")
    
    image.size = int(image.size)
    if (image.size >= 2000):
        await start_external_process(image)
    
    elif (image.size >= 1000):
        backgroundtasks.add_task(process_file_in_background)
    else:
        print(f"processing file in request task")
        await process_file_in_background()

