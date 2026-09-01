## Lab Responses
In this lab you will will change the previous created API endpoint to correctly return status codes.
> duration: 30 minutes

### Step 1. Copy over the previous exercise 
Navigate to your lab folder and create a new project with uv, name it responses.

Dont forget to add packages HTTPie, Pydantic and fastapi[standard] to your project using uv add. 

Make sure the project is created without package (--no-package) and the main.py is empty. 

Copy over the main.py from the last requestparameters exercise. 

### Step 2. Implement the response codes correcly

For each of the endpoints we wrote earlier, try to implement the correct response codes.

If you are done, run the project using
```
uv run fastapi dev
```

Let the server start and reload whenever you write code. 

### Step 3. Implement Error Status codes
Examine each endpoint and find out if there are dynamic or error status codes that are applcicable. For instance, what happens when the photo that is added, is too large or of a wrong type?

To be more specific, adjust each endpoint so they have the correct status response code:
- [POST] (users/add) => returns a 201 created
- [GET] (users/search) => returns a 200 ok
- [DELETE] (users/delete) => returns either a 204 no content on success or a 404 not found when the user does not exist
- [POST] (users/profile/photo) => returns a 201 created or a 400 bad request when the photo is not of the correct type (image/jpg). In the _starter directory you can find a valid file to test your upload with
- [POST] (users/login) => returns a 200 ok
- [GET] (users/me) =>returns a 200 ok or a 401 unauthorized when no cookie is provided

### Extra Exercise
For all the endpoints that are applicable, make sure that all statuscodes that could be returned are all documented correcly in the OpenAPI specification.

Check the docs for the OpenAPI status codes to see the effect of your additions.

### Summary
We have defined and implemented correct REST status codes and added all possible status codes to the OpenAPI specification!

Congrats!

-= End of lab =-
  
