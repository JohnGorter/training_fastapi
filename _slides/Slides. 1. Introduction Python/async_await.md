# Async/Await

---
### Concepts of async

Synchronous code execution processes operations sequentially, 
blocking the thread until each task completely finishes. 

This rigid, linear execution model introduces severe performance, user experience, and hardware efficiency bottlenecks
    - CPU Idle Time (I/O Blocking)
    - Unresponsive User Interfaces
    - Head-of-Line Blockinghung request delays every unrelated task queued behind it, causing cumulative - Severe Scalability Limits
    - Low Throughput

---
### An example
    
    McDonalds serves happy meals:
    - More casiers equal to more througput
    - More kitchen employees equal to shorter latency

    But do we have to wait until everything is done or can we get
    notified when they are done preparing our meal => implement a callback!

---
### Callbacks

Callbacks give us the option to 
- complete a task when our request is finished

Callbacks give the thread
- time to do other meaningfull code in the meantime

This even works when there is 1 cashier/employee
Reduce the wait time!

---
### Callbacks

Do callbacks scale? 
No not really

Even though there is no wait time, we still have a single cashier!


---
### Parallelism

To be more schalable, we have to:
- split the process in independent tasks that can be executed in parallel
- add mode cpus/cores of cashiers/employees

Burgers and Fries can be baked independently while the salad preparation is in effect!
We cannot get faster that the time it takes to do the longest independent task (latency), 
but with more cpu's/cores, we can execute multiple requests simultanously (througput).

---
### Paralellism

For the benefit of efficiency to be able to execute more work and minimize wait times, 
or with other words: make use of the hardware capabilities: 
- we still use callbacks in the execution of tasks

So even though they are unrelated, they have a shared important benefit: 
- they are key ingredients to make a scalable, performant and efficient system

---
### Callbacks in Python

Python supports callbacks: 

```
def process_user(user_id, callback):
    # Simulate fetching user data
    user_data = {"id": user_id, "name": "Alex"}
    callback(user_data)


process_user(101, lambda user: print(f"User loaded: {user['name']}"))
```

So we can implement concurrency easily

---
### Demo callbacks 

---
### Concurrency 

Concurrency is about structural design 
- handling multiple tasks by interleaving execution
Paralellism is about physical execution
- running multiple tasks simultaneously on separate hardware cores

---
### Core Differences


|Feature|Concurrency|Parallelism|
|---|---|---|
|Core Concept|Managing multiple tasks at once|Executing multiple tasks simultaneously|
|Hardware Need|Single core (via time-slicing) or multi-core|Requires multiple CPU cores or processors|
|Primary Benefit|High responsiveness and non-blocking I/O|High throughput and reduced processing latency|
|Ideal Use Case|I/O-bound operations (web servers, database queries)|CPU-bound operations (data rendering, AI training)|

Python
- async and await are core language keywords built directly into Python's syntax
- asyncio is a standard library module that provides an event loop engine.

---
### Core Distinctions

Keywords vs. Library Features: Just like def, if, or try, the keywords async and await are part of Python's grammar (introduced natively in Python 3.5). CPython parses them directly without needing any import statements.

---
### Core Distinctions

Native Coroutine Creation: Writing async def my_func(): pass creates a native CPython coroutine object under the hood. The language handles pausing and resuming the function frame internally.

---
### Core Distinctions

Event Loop Independence: The async/await syntax doesn't care how a coroutine is executed. While asyncio is Python's built-in event loop engine, alternative frameworks like trio or curio can run async/await code using their own event loops.

---
### Core Distinctions
Implicit Loop Management: In frameworks like FastAPI, Starlette, or Django, the underlying ASGI web server (such as Uvicorn or Hypercorn) manages the asyncio event loop for you in the background. It calls your async def endpoints directly, so you rarely need to interact with asyncio explicitly in application code.