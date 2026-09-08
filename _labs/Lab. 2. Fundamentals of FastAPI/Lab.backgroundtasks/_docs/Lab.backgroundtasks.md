## Lab Backgroundtasks
In this lab you will simulate an endpoint that receives a request for processing a file and sending an e-mail conditionally.
> duration: 30 minutes

### Step 1. Create a new project 
Navigate to your lab folder and create a new project with uv, name it lab_backgroundtasks.
Make sure the project is created without package (--no-package) and the main.py is empty. 

```
uv init --no-package lab_backgroundtasks
```

Dont forget to add packages HTTPie, Pydantic, Pydantic[email], fastapi[standard] and aiosmptd to your project using uv add. 

```
uv add "fastapi[standard]"
uv add pydantic
uv add "pydantic[email]"
uv add HTTPie
uv add aiosmtpd
```

Copy over the all files from the _starter folder in this lab.

Take your time to inspect the code.

You have to write an enpoint that takes a user submission of a file to upload. It is your job to check to see if 
the file is of an acceptable size and valid for processing as an image. 

If the file is not an image, you should throw a bad request error.
If the filesize is not known, you should throw a bad request error.
If the file is larger than 100kb, we have to hand-off this file processing to a background task. 
If the file is larget than 250kb, we have to hand-off this file processing to an external service. 

When the processing is completed, we want to inform the user of this by sending an email. 

In this lab we are going to implement the functionality from above. 

### Step 2. Implement the endpoint

In the root of the directory, open the main.py file and 
try to implement the logic that is described in the task above. 

There are already imported functions for the backgroundtask and the external process handling. 

```
 # you can use the external process function like this:
await start_external_process(image)
# you can use the process_file_in_background like this:
backgroundtasks.add_task(process_file_in_background)
```

If you need inspiration, you can look at the solution <a href="../_solution/main.py"> here </a>

If you are done, run the project using the steps in the next exercise.

### Run the setup

For this exercise, you need 3! terminals that are sourced into your environment:
- the first terminal mimics an e-mail smtp server
- the second terminal runs your fastapi server
- the third terminal is for executing HTTPie commands to test the request processing

In the first terminal you start, make sure you activate the environment using
```
source .venv/bin/activate
```

Wait for the activation to succeed.
Then issue this command to launch a fake HTTP server
```
python -m aiosmtpd -n -c aiosmtpd.handlers.Debugging -l localhost:1025
```

Then, when te server is started, start the second terminal start the fastAPI server using
```
uv run fastapi dev
```

Wait for the server to start. 

Lastly, start the last terminal and then activate the virtual environment using
```
source .venv/bin/activate
```

Wait for it to complete and then issue the following command
```
http -f POST localhost:8000 image@mail.jpg
```

Test to see if the submission is accepted, then visit each of the terminals you have opened to check if the logs
showed a correct working request processing. 

### Extra Exercise
- there is no extra exercise in this chapter -

### Summary
We have successfully implemented code to start a background task or an external process to start the processing of images. This exercise introduced the topic of background hand-off.

Congrats!

-= End of lab =-
  
