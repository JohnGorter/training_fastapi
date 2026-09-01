# Sessions

---
### Sessions






In this blog, we’ll cover how to implement a simple session validation system in FastAPI. Sessions help you manage user authentication without repeatedly asking users for their credentials, and we’ll show you how to create a user dependency that validates a session before allowing access to certain API routes.

Our goal is to explain how to create a valid session or user dependency with FastAPI in a simple, beginner-friendly way. Let’s dive in!

What You Will Learn
Session Management in FastAPI: How to create and manage sessions using cookies.
Creating a Session Validation Dependency: How to create a reusable dependency for validating sessions.
Handling Token Expiry: How to check for expired tokens.
Setting Up the Project
Here’s a step-by-step guide to set up FastAPI using Python’s virtual environment from scratch, starting with creating the project directory and initializing everything.

1. Create a Project Directory
First, open your terminal and create a new directory for your FastAPI project:

mkdir app
Navigate into the project directory:

cd app
2. Set Up a Virtual Environment
To keep your project dependencies isolated, use Python’s venv module to create a virtual environment. Run the following command:

python -m venv venv
This will create a folder called venv inside your project directory, which contains the virtual environment files.

3. Activate the Virtual Environment

Next, activate the virtual environment to ensure that any packages you install will be specific to this project:

On Windows:

venv\Scripts\activate
On macOS/Linux:

source venv/bin/activate
Once activated, you’ll see (venv) at the beginning of your terminal prompt, indicating the environment is active.

pip install fastapi uvicorn
5. Create the Project Structure

Let’s now create the project structure with the necessary directories and files. In the terminal, run the following commands to create a basic structure:

mkdir session
touch main.py
touch session/session_layer.py
This will create an app directory with a main.py file (for the main FastAPI app) and a session directory with a session_layer.py file for your session management logic.
Now the project structure looks like this:

my_fastapi_project/
│
├── app/
│   ├── main.py
│   └── session/
│       └── session_layer.py
└── venv/
6. Write Your FastAPI Code

Now, open app/main.py and start by writing a basic FastAPI app:

# app/main.py

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}
7. Run the FastAPI App
You can now run your FastAPI app using Uvicorn. In your terminal, run:

uvicorn app.main:app --reload
Let’s work on actual code !
Creating Random Session Strings
In a session-based authentication system, each user gets a session ID. To ensure each session ID is unique, we’ll generate a random session string using Python’s secrets module.

# app/session/session_layer.py

import secrets

def create_random_session_string() -> str:
    return secrets.token_urlsafe(32)  # Generates a random URL-safe string
Here, we use secrets.token_urlsafe() to generate a random 32-character session string. This string is unique for each session and will be stored in the user’s cookies.

2. Validating Sessions

The next step is to ensure that the session is valid when a user makes a request. This is where the session validation function comes into play. It checks for a session ID and access token in the request’s cookies and session data.

# app/session/session_layer.py

from fastapi import Request
import logging

def validate_session(request: Request) -> bool:
    session_authorization = request.cookies.get("Authorization")
    session_id = request.session.get("session_id")
    session_access_token = request.session.get("access_token")
    token_exp = request.session.get('token_expiry')

    if not session_authorization and not session_access_token:
        logging.info("No Authorization and access_token in session, redirecting to login")
        return False
    
    if session_authorization != session_id:
        logging.info("Authorization does not match Session Id, redirecting to login")
        return False
    
    if is_token_expired(token_exp):
        logging.info("Access_token is expired, redirecting to login")
        return False
    
    logging.info("Valid Session, Access granted.")
    return True
Explanation:

We retrieve Authorization, session_id, and access_token from the request cookies and session.
The function checks if the session is valid by ensuring:
The session ID matches the stored session.
The access token is not expired.
If any of these conditions fail, we log the issue and return False.

3. Checking Token Expiry

Sessions often have an expiration time. We’ll now create a helper function to check if the token has expired.

# app/session/session_layer.py

from datetime import datetime

def is_token_expired(unix_timestamp: int) -> bool:
    if unix_timestamp:
        datetime_from_unix = datetime.fromtimestamp(unix_timestamp)
        current_time = datetime.now()
        difference_in_minutes = (datetime_from_unix - current_time).total_seconds() / 60
        return difference_in_minutes <= 0
    
    return True
Explanation:

This function converts the Unix timestamp (which represents the token’s expiry time) into a datetime object.
It checks whether the current time has surpassed the token expiration time.
If the token is expired, it returns True; otherwise, False.
4. Implementing the Session Validation in an API

Once the session validation logic is ready, we can use it as a dependency in our API routes. Here’s an example of using it to protect an endpoint:

# app/main.py

from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from app.session.session_layer import validate_session

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key='some-secret-key')

@app.get("/some-api")
async def some_api(request: Request, is_valid_session: bool = Depends(validate_session)):
    if not is_valid_session:
        return RedirectResponse("/logout", status_code=303)
    
    return {"message": "Welcome to the protected route!"}
Explanation:

We use the Depends() function to inject our validate_session() function as a dependency.
If the session is invalid, the user is redirected to the /logout endpoint.
The SessionMiddleware is added with app.add_middleware(). Make sure to replace "your-secret-key" with a strong, unique secret key for encrypting session data.
5. Handling Logout

The logout process should clear the session and remove the relevant cookies.

# app/main.py

@app.get("/logout")
async def logout(request: Request, response: RedirectResponse):
    request.session.clear()
    response.delete_cookie(key="Authorization")
    return RedirectResponse("/login", status_code=303)
Explanation:

We clear the session data and delete the Authorization cookie to log the user out.
6. Setting Up a Session on Login

Finally, when the user logs in, we create a session and store the session ID and token expiry in the session.

# app/main.py

@app.post("/login")
async def login(request: Request, response: RedirectResponse):
    session_id = request.session["session_id"] = create_random_session_string()
    request.session["token_expiry"] = some_expiry_time  # Token expiry logic
    response.set_cookie(key="Authorization", value=session_id)
    return RedirectResponse("/some-api", status_code=303)
NOTE : Here, a session ID and token expiry are created when the user logs in, and the session ID is stored in a cookie.
You need to add your logic about how you get it from authentication process !

Conclusion
In this blog, we’ve shown how to create a simple session management system in FastAPI. You’ve learned how to:

Generate random session strings.
Validate sessions using a custom FastAPI dependency.
Handle token expiration.
Manage login and logout functionality.
This approach can be expanded upon to meet more complex session requirements, but it serves as a great starting point for adding session management to your FastAPI applications.

Need More Help?
If you have any questions or need further assistance with FastAPI or any other topic, feel free to reach me out:

Twitter (X): @eyeofmaaz
LinkedIn: Maaz Bin Mustaqeem
I’ll be happy to help!