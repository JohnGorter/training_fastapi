## Lab Responses
In this lab you will will change the previous created API endpoint to correctly return status codes.
> duration: 30 minutes

### Step 1. Copy over the previous exercise 
Navigate to your lab folder and create a new project with uv, name it lab_responses.
Make sure the project is created without package (--no-package) and the main.py is empty. 

```
uv init --no-package lab_responses
```

Dont forget to add packages HTTPie, Pydantic, Pydantic[email] and fastapi[standard] to your project using uv add. 

```
uv add "fastapi[standard]"
uv add pydantic
uv add "pydantic[email]"
uv add HTTPie
```

Copy over the main.py from the _solution folder in this lab to the root of your project
 
### Step 2. Implement the response codes correcly

For each of the endpoints we wrote earlier, try to implement the correct response codes.

Here are the requirements:
- /users/add => should respond with HTTP_201_CREATED
- /users/search => should respond with HTTP_200_OK 
- /users/profile/photo => should respond with HTTP_201_CREATED 
- /users/login => should respond with HTTP_200_OK 
- /users/me => should respond with HTTP_200_OK 


If you are done implementing, run the project using
```
uv run fastapi dev
```

Let the server start and reload whenever you write code. 

### Step 3. Implement Error Status codes

Examine each endpoint and find out if there are dynamic or error status codes that are applicable. For instance, what happens when the photo that is added, is too large or of a wrong type?

To be more specific, adjust each endpoint so they have the correct status response code:
- [DELETE] (users/delete) => returns either a 204 no content on success or a 404 not found when the user does not exist
- [POST] (users/profile/photo) => returns a 201 created or a 400 bad request when the photo is not of the correct type (image/jpg)
Note: In the _starter directory you can find a valid file to test your upload with
- [GET] (users/me) =>returns a 200 ok or a 401 unauthorized when no cookie is provided

After changing the code, test the endpoints with HTTPie and the commands that are added in the comment at the top of the endpoint.

### Extra Exercise
For all the endpoints that are applicable, make sure that all statuscodes that could be returned are all documented correcly in the OpenAPI specification.

Here is an example
```
responses={404: {"description": "User not found"}})
```

Check the docs for the OpenAPI status codes to see the effect of your additions.

### Summary
We have defined and implemented correct REST status codes and added all possible status codes to the OpenAPI specification!

Congrats!

-= End of lab =-
  
