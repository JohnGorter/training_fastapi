## Lab Responsemodels
In this lab you will change the previous created API endpoint to correctly validate and serialize models in your business log API endpoints.
> duration: 30 minutes

### Step 1. Copy over the previous exercise 
Navigate to your lab folder and create a new project with uv, name it lab_responsemodels.
Make sure the project is created without package (--no-package) and the main.py is empty. 

```
uv init --no-package lab_responsemodels
```

Dont forget to add packages HTTPie, Pydantic, Pydantic[email] and fastapi[standard] to your project using uv add. 

```
uv add "fastapi[standard]"
uv add pydantic
uv add "pydantic[email]"
uv add HTTPie
```

Copy over the main.py from the _starter folder in this lab.

Take your time to inspect the code and notice there is a lot of model interaction in the input and the output of the API. 

The comments at the top show the details of how you would test the endpoint with the corrent HTTPie
command, here is an example
```
# http --form POST localhost:8000/users/add firstname=john lastname=gorter password=jojo
@app.post("/users/add", status_code=status.HTTP_201_CREATED, response_model=UserResponseAction)
```

Notice also that in the import lines, the models are imported but missing...

It is your job to create the correct models (./models.py) for this code to work!

### Step 2. Implement the models correcly

In the root of the directory, create a file named ./models.py and 
try to implement the models that belong to the API endpoints. 

You should be able to retrieve all the necessary details from the usage of the API definitions in the ./main.py file. This time we took the right approach to split the input models from the response models!

If you need inspiration, you can look at the solution <a href="../_solution/models.py"> here </a>


If you are done, run the project using
```
uv run fastapi dev
```

Test to see if it all worked.

### Extra Exercise
Make an enpoint for the changepassword action, this enpoint should accept an email address for the user and three passwords, the first one is the old original password, the two other passwords are the new and the repeated new password that should be identical. 

Here is inspiration
```
# http -f POST localhost:8000/users/changepassword user=john@test.nl password=123 new_password=123 repeat_new_password=456
# http -f POST localhost:8000/users/changepassword user=john@test.nl password=123 new_password=456 repeat_new_password=456
@app.post("/users/changepassword", status_code=status.HTTP_200_OK, response_model=ChangePasswordResponse)
async def change_password(change_password: Annotated[ChangePassword, Form()]):
    return {"user": change_password.user, "status": "password changed"}
```

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
  
