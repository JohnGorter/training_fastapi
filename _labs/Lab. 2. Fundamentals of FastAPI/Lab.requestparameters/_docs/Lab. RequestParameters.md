## Lab RequestParameters
In this lab you will make a set of API endpoints with arguments that actually resemble a real life implementation
> duration: 25 minutes

### Step 1. Create a new project in a working folder for your labs
Navigate to your lab folder and create a new project with uv, name it requestparameters. 
Dont forget to add packages HTTPie, Pydantic and fastapi[standard] to your project using uv add. 
Make sure the project is created without package (--no-package) and the main.py is empty. 

### Step 2. Write the fastAPI boilerplate code
Open the main.py and write the boilerplate code to generate a fastAPI server. 
Try to run the server using
```
uv run fastapi dev
```

Let the server start and reload whenever you write code. 

### Step 3. Add user endpoints

Define async methods to:
- [POST] (users/add) => add users to a list of users using a form with firstname, lastname and password
- [GET] (users/search) => get users with a query parameter that queries for a (part of a) name
- [DELETE] (users/delete) => delete users given his/her name in the querystring.
- [POST] (users/profile/photo) => add profile photo to the user, given the username in the form that is POSTED
- [POST] (users/login) => let a user login using his firstname and password and setting a cookie on response
- [GET] (users/me) => get the user that is logged in using the cookie in the request. The cookie holds the username, so get it from there and return it in the response

For now you dont have to really implement the business logic for the methods. You dont actually have to save user to a list. 

### Step 4. Execute commands using HTTPie

Use HTTPie to test each individual API Call with the correct syntax.

### Extra Exercise
Try to implement the business logic using regular Python syntax and utillities like in-memory dicts and lists. 


### Summary
We have defined and run multiple different API endpoints with different carriers of metadata for the request, ranging from query string to cookies.

Congrats!

-= End of lab =-
  
