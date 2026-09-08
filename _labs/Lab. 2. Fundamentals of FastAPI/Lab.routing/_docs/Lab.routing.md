## Lab Sessions
In this lab you will use sessions to implement state over multiple endpoint requests.
> duration: 30 minutes

### Step 1. Start a new project
Navigate to your lab folder and create a new project with uv, name it lab_routing.
Make sure the project is created without package (--no-package) and the main.py is empty. 

```
uv init --no-package lab_routing
```

Dont forget to add packages HTTPie, Pydantic, Pydantic[email] and fastapi[standard] to your project using uv add. 

```
uv add "fastapi[standard]"
uv add pydantic
uv add "pydantic[email]"
uv add HTTPie
```

Copy over all the files from the _starter folder in this lab.

Take your time to inspect the code and notice there are blog and user endpoints. The structure should match the 
folling routing schema: 
- a route to get all users => /users/
- a route to get a specific user => /users/{user_id}
- a route to get all the blogs from a user => /users/{user_id}/blogs/
- a route to get a specific blog from a specific user => /users/{user_id}/blogs/{blog_id}
- a route to get all blogs => /blogs/
- a route to get a unique blog by id => /blogs/{blog_id}

Implement the logic to define and register these routes correctly!

If you are done, run the project using
```
uv run fastapi dev
```

Test to see if it all worked with the following HTTPie commands
```
http localhost:8000/users/
http localhost:8000/users/10
http localhost:8000/users/10/blogs/
http localhost:8000/users/10/blogs/1
http localhost:8000/blogs/
http localhost:8000/blogs/10
```

Did all the endpoints work? Great!

### Extra Exercise
Add endpoints and routing to get all comments that come with a blog. 
These comments should not be available as root routes, only as sub routes from the blog route, like this:

```
http localhost:8000/users/10/blogs/1/Comments/
http localhost:8000/blogs/10/Comments/
```

Try out the endpoint and see if all went correctly. 

### Summary
We have built routing to modulerize rest endpoints to different 'domains' of our application.
Congrats, you are now a routing master!

-= End of lab =-
  
