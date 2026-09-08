## Lab Sessions
In this lab you will add data to a session cookie and get it from a session cookie to maintain state.
> duration: 30 minutes


### Step 1. Create a new project 
Navigate to your lab folder and create a new project with uv, name it lab_sessions.
Make sure the project is created without package (--no-package) and the main.py is empty. 

```
uv init --no-package lab_sessions
```

Dont forget to add packages HTTPie, Pydantic, Pydantic[email] and fastapi[standard] to your project using uv add. 

```
uv add "fastapi[standard]"
uv add pydantic
uv add "pydantic[email]"
uv add HTTPie
```

We are now going to make everything from scratch, no starter files to copy over.
In this lab, try to create a shoppingcart using Pydantic models and make a ShoppingCart model.


Here is the code: 
```
class ShoppingCart(BaseModel):
    items:List[ShoppingCartItem]

class ShoppingCartItem(BaseModel):
    product:str
    amount:int
    price:float
```

Create the endpoints to add, remove and return the shoppingcart to the client. 

Note: you need to store and read the shopping cart data to and from the cookie that
is part of the response/request. 

After you have completed to add the code, run the project using:
```
uv run fastapi dev
```

Note: if things do not fall into place directly, peek at <a href="../_solution/main.py"> this file</a>.

### Step 2. Serverside Sessions

Use the same example as in the previous exercise, but now only store a generated sessionid into the cookie. 
Store the ShoppingCart data in a dict on the server. 

You also should keep the session-id and the instance of the ShoppingCart in sync. 

For now you dont have to implement threadsafety or memorysweeping. Just use a dictionaty and store the sensitive data in fast, secure RAM on the server. 

After you have completed to add the code, run the project using:
```
uv run fastapi dev
```

Note: if things do not fall into place directly, peek at <a href="../_solution/main.py"> this file</a>.


### Extra Exercise

Implement a thread safe version of the ShoppingCart session logic. Use the slides as reference for the solution.

After your changes, try to run the code again using HTTPie as a tool. Does everything still work?

### Summary
We have successfully created a session, first in cookie, but later in serverside storage! Well done!

Congrats!

-= End of lab =-
  
