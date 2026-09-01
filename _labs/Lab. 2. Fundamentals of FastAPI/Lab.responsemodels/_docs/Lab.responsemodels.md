## Lab Responsemodels
In this lab you will change the previous created API endpoint to correctly validate and serialize models in your business log API endpoints.
> duration: 30 minutes

### Step 1. Copy over the previous exercise 
Navigate to your lab folder and create a new project with uv, name it responsemodels.

Dont forget to add packages HTTPie, Pydantic and fastapi[standard] to your project using uv add. 

Make sure the project is created without package (--no-package) and the main.py is empty. 

Copy over the main.py from the _starter folder in this lab.

Take your time to inspect the code and notice there is a lot of model interaction in the input and the output of the API. Notice also that in the import lines, the models are imported but missing...

### Step 2. Implement the models correcly

In the root of the directory, create a file named ./models.py and 
try to implement the models that belong to the API endpoints. 

You should be able to retrieve all the necessary details from the usage of the API definitions in the ./main.py file. 

If you are done, run the project using
```
uv run fastapi dev
```

Test to see if it all worked.

### Extra Exercise
Make an enpoint for the changepassword action, this enpoint should accept an email address for the user and three passwords, the first one is the old original password, the two other passwords are the new and the repeated new password that should be identical. 

Make a model (ChangePassword) that maps on this input with:
- user: EmailStr
- password: str
- new_password: str
- repeat_new_password: str

Make sure you check that the two new passwords are identical on validation of the input and throw an error if it is incorrect. 

Return a ChangePassordResult that shows the email address of the user and the result status code, fail or success.

### Summary
We have defined and implemented correct REST status codes and added all possible status codes to the OpenAPI specification!

Congrats!

-= End of lab =-
  
