import time
from fastapi import FastAPI, BackgroundTasks
from pydantic import EmailStr, BaseModel

app = FastAPI()

def send_welcome_email(email: str):
    # Simulate slow SMTP network transmission
    time.sleep(2.0)
    print(f"[BACKGROUND] Welcome email sent successfully to {email}")

class UserSignup(BaseModel):
    email: EmailStr

@app.post("/signup", status_code=202)
async def signup_user(
    payload: UserSignup, 
    background_tasks: BackgroundTasks
):
    # Schedule background execution
    background_tasks.add_task(send_welcome_email, email=payload.email)

    # Returns immediately to client while email sends in background
    return {"status": "accepted", "message": "Account created. Email processing."}
