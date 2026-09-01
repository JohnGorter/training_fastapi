# Demo 1. Overview

### Step 1. New Project
create a new project named demo_httpie using
```
uv init --no-package demo_httpie
```

### Step 2. Add fastAPI and HTTPie
add fastAPI to the package using
```
uv add "fastapi[standard]"
```
and add HTTPie to the package using
```
uv add "HTTPie
```

### step 3. default fastAPI
create a default hello world FastAPI application with a root (/) endpoint

### step 4. Run the server
run the code using uv run fastapi dev, make sure the server is up and running

### Step 5. Show error
open a second terminal and first show that the command does not work
```
http localhost:8000/
```

### Step 6. Make it work
now activate the .venv using
```
source .venv/bin/activate
```
notice that the prompt now changes so you see the .venv is activated

### Step 7. Re-execute the code
execute the command: 
```
http localhost:8000/
```
show the output and notice JSON decoding

### Step 8. More options

show more options like
```
http -b
http -v
```

explain their uses!

