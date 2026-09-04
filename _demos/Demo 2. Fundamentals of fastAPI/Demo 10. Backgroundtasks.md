# Demo 10. Backgroundtasks

### step 1. Open the demo folder and copy over the following code in main.py

This code actually simulates sending an email after an endpoint was called
The email send procedure, for testing purposes, takes 2 seconds to process!

```
import time
from fastapi import FastAPI, BackgroundTasks, status
from pydantic import BaseModel, EmailStr

app = FastAPI()

def send_welcome_email(email: str):
    # Simulate slow SMTP network transmission
    time.sleep(10.0)
    print(f"[BACKGROUND] Welcome email sent successfully to {email}")

class UserSignup(BaseModel):
    email: EmailStr

# http POST localhost:8000/signup email=hello@test.nl
@app.post("/signup", status_code=status.HTTP_202_ACCEPTED)
async def signup_user(
    payload: UserSignup, 
    background_tasks: BackgroundTasks
):
    # Schedule background execution
    background_tasks.add_task(send_welcome_email, email=payload.email)

    # Returns immediately to client while email sends in background
    return {"status": "accepted", "message": "Account created. Email processing."}

```
