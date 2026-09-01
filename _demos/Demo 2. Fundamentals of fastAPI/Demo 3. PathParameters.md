# Demo 3. PathParameters

### step 1. open the project in demo_pathparameters and source the virtual environment in your terminal
```
source .venv/bin/activate
```

### step 2. test the first enpoint by issuing
```
http localhost:8000/items/10
```

show the result and explain the type coersion

### step 3. test the first endpoint with an invalid type in its path
```
http localhost:8000/items/john
```

### step 4. show the documentation by visiting url
```
http://127.0.0.1:8000/docs
```

Try the API in the Swagger interface

### step 5. show that ordering matters 

issue the command
```
http localhost:8000/users/me 
```

Explain why the response shows "me" instead of "the current user"
Now change the order of the paths to show a correct result

### step 6. show enum documentation

Navigate to 
```
http://localhost:8000/docs
```
and show the enum that is used form the models endpoint (models/{model_name})

### Step 7. Show the files path path parameter

Navigate to url
```
http://localhost:8000/files//john/john/john/john/txt
```

And show the result
