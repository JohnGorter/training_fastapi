## Lab nosql
In this lab you will add data to a nosql database, namely MongoDB
> duration: 30 minutes

### Step 0. Install MongoDB

Install MongoDB using the steps you can find online for the plafform/OS you run on. 

### Step 1. Create a new project 
Navigate to your lab folder and create a new project with uv, name it lab_nosql.
Make sure the project is created without package (--no-package) and the main.py is empty. 

```
uv init --no-package lab_nosql
```

Dont forget to add packages HTTPie, Pydantic, Pydantic[email], fastapi[standard] and pymongo[srv]>=4.9 to your project using uv add. 

```
uv add "fastapi[standard]"
uv add pydantic
uv add "pydantic[email]"
uv add HTTPie
uv add "pymongo[srv]>=4.9"
```

Copy over the all files from the _starter folder in this lab.

Take your time to inspect the code.

I gave you all the code to connect to a MongoDB dabase server that runs locally. Time for you to connect the endpoints to the database logic. 
If you inspect the main.py code, you see "your code here" comments.

Try to implement all the logic to insert, query, patch and delete items to/from the database. 

After you have completed to add the code, run the project using
```
uv run fastapi dev
```

Note: if things do not fall into place directly, peek at <a href="../_solution/main.py"> this file</a>.

### Step 2. Test the endpoints

Use HTTPie to test all the enpoints from the main.py file. Did they all work as expected?

### Extra Exercise

The code is not really layered correctly, try to implement a service and a data layer and move the code in the appropriate layers. 
This makes for a better manageable, modular code base.

After your changes, try to run the code again using HTTPie as a tool. Does everything still work?

### Summary
We have successfully connected the fastAPI code to the database and made CRUD calls to the database to persist data!
Congrats!

-= End of lab =-
  
