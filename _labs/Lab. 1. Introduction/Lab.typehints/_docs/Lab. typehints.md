## Lab 1. Basic Setup
In this lab you will experiment with typehints in python
> duration: 30 minutes

### Step 1. Create a new Project
Navigate to your Labs directory, which you have created earlier in the labs. 
Execute the following command
```
uv init typehints --no-package
```

CD into your new project and use uv th add the package mypy. I guess you knwo the command by now, but if you don't, here is the command anyways:

```
uv add mypy
```

Edit the main.py so it has the following code: 

```
def add_numbers(a: int, b:str) -> int
  return a * b

print(add_numbers(10, 10))
```

Save and run the code with the following command: 

```
uv run main.py
```

Notice how the runtime does not complain at all and just runs the code fine!
Type checking does not occur at run time, it is an aid online at development time. 

Run the code using the mypy package:
```
uv run mypy main.py
```

Notice how now there are type errors? This is much better, but we want even more support. 
Why don't we enable this typechecking while we are coding in the IDE, directly at our fingertips so we never forget to typecheck again...

### Step 2. Install VSCode extensions
Click on the extension tabs and install the following extensions from the marketplace:
- Python Debugger
- Python
- Pylance
- Python environments

If they are succesfully installed, re-open your project in Visual Studio. There should be a popup that asks to enable type hinting support. Say yes and see how the errors are now shown in the IDE while we are coding, much better!

### Step 3. Add typings
Copy the code in exercise 1 in the folder _starterfiles in this lab directory from the exercise1.py and paste it into your own file. Note that there are no typehints at all. Try to make the code type safe by adding typehinst to the functions and variables. 

If you are done, try to compare them with the exercise1.py from the _solution folder in this lab. Did you manage to get it all correct? 

### Step 4. Generic typings
Copy the exercise2.py from the _starterfiles directory and read the comments in the starter file, the challenges are explained in detail in that file. For completeness, they are described here also. 

Exercise 4.1 Create two typed functions that take a list:
- the first function should filter the list based on a condition and return a new list
- the second function should transform the list based on a condition and return a new list

Exercise 4.1.1 test the functions with a list of strings and a list of integers

Exercise 4.2 Create a Person class with name and age attributes and test your previously created functions with a list of Person objects and make sure to use the where function to filter the list of Person objects based on a condition and the select function to transform the list of Person objects to strings.

Exercise 4.3 Create a LINQ class that takes a list and has two methods: where and select. 
- each method should take a function as an argument and return a new LINQ object with the filtered or transformed list.
- therefore we can use autocompletion to chain the methods together.

Make sure to use correct typing for the class and its methods.

Exercise 4.3.1 test the LINQ class with the Person class where you create a LINQ object with a list of strings and then use the where method to filter the list based on a condition and the select method to transform the list to a list of Person objects.
The condition for the where method should be that the length of the string is greater than 3 and the select method should 
create a Person object with the name being the string and the age being the length of the string multiplied by 10.

Use your knowledge to work out the challenges for that file. 

### Summary
We have played around with the basics of type hinting, you know enough to proceed to the next chapter.

Congrats!

-= End of lab =-
  
