## Lab nosql
In this lab you will add data to a sqlite database
> duration: 30 minutes

### Step 1. Create a new project 
Navigate to your lab folder and create a new project with uv, name it lab_sqlite.
Make sure the project is created without package (--no-package) and the main.py is empty. 

```
uv init --no-package lab_sqlite
```

Dont forget to add packages HTTPie, Pydantic, Pydantic[email], fastapi[standard] and aiosqlite to your project using uv add. 

```
uv add "fastapi[standard]"
uv add pydantic
uv add "pydantic[email]"
uv add HTTPie
uv add aiosqlite
```

Copy over all the files from the _starter folder in this lab.

Take your time to inspect the code.

Write the code to talk to the database. You should fill in the code that is marked with 
```
# your code here
```

After you have completed to add the code, run the project using
```
uv run fastapi dev
```

Note: if things do not fall into place directly, peek at <a href="../_solution/main.py"> this file</a>.


### Step 2. Test the endpoints

Use HTTPie to test all the enpoints from the main.py file. Did they all work as expected?

### Extra Exercise

-= no extra excercise =-

### Summary
We have successfully connected the fastAPI code to the sqlite database and made CRUD calls to the sqlite database to persist data!
Congrats!

-= End of lab =-
  
