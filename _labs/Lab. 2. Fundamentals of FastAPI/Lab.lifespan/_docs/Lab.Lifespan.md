## Lab Lifespan
In this lab you will write server startupcode and shutdowncode using a lifespan.
> duration: 10 minutes

### Step 1. Create a new project 
Navigate to your lab folder and create a new project with uv, name it lab_lifespan.
Make sure the project is created without package (--no-package) and the main.py is empty. 

```
uv init --no-package lab_lifespan
```

Dont forget to add packages HTTPie, Pydantic, Pydantic[email], fastapi[standard] and aiosmpt to your project using uv add. 

```
uv add "fastapi[standard]"
uv add HTTPie
```

Copy over the main.py from the _starter folder in this lab.

Take your time to inspect the code.

The requirement is to log startup code in the beginning of the server initialisation steps. 
Write a @contextmanager decorated generator function that prints "server started" upon start and
"server stopped" when the server shuts down. 

Then start the server from the terminal using
```
uv run fastapi dev
```

Wait for the server to start.

Did you see your message in the log upon startup?

If it did not work, check your version with the version in the solution <a href="../_solution/main_exercise1.py">here</a>

### Step 2. Implement data carriage

Change the code so upon start, you set the something attribute on the app.state to a value:
```
 app.state.something = "Initialized"
```

also set the state to none when the server shuts down:
```
 app.state.something = None
```

In the last step, get the something value in the request using a request dependency and the following code:
```
request.app.state.something
```

Make sure this value is added to the response JSON. 

Start the server again, if it is not started already and use the following command to test to see if the value was carried over
```
http localhost:8000
```

Does it work as expected? If not, compare your version with this one <a href="../_solution/main_exercise2.py">here</a>

### Extra Exercise

Try to implement a try: finally: block and throw an error from the request handler. Make sure the code from the finally block in the lifespan generator fires!

### Summary
We have successfully implemented code to setup and tear down logic on the server. In later topics we see this pattern used for access to databases!

Congrats!

-= End of lab =-
  
