from fastapi import FastAPI, Form, HTTPException, UploadFile, status, BackgroundTasks
from typing import Annotated
from mymail import sendEmail
from utils import start_external_process, process_file_in_background

app = FastAPI()

@app.post("/image")
async def processImage(image: Annotated[UploadFile, Form()], backgroundtasks:BackgroundTasks):
    # your code here
    pass