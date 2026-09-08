from fastapi import FastAPI, File, HTTPException, UploadFile, status, BackgroundTasks
from typing import Annotated
from mymail import sendEmail
from utils import start_external_process, process_file_in_background

app = FastAPI()

@app.post("/image")
async def processImage(image: Annotated[UploadFile, File()], backgroundtasks:BackgroundTasks):
    # your code here
    pass