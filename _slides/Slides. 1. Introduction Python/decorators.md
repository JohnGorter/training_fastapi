# Decorators 


---
### What are Decorators 

*Decorators are a flexible way to modify or extend behavior of functions or methods, without changing their actual code*

---
### What is a decorator technically


A decorator is essentially 
- a function that takes another function as an argument 
- returns a new function with enhanced functionality

They are often used in scenarios such as logging, authentication and memoization

---
### Decorator Example
 
Below is an example to demonstrate how decorator functions:
```
def decorator(func):
    def wrapper():
        print("Before calling the function.")
        func()
        print("After calling the function.")
    return wrapper
​
@decorator
def greet():
    print("Hello, World!")
greet()
```
```
Output
Before calling the function.
Hello, World!
After calling the function.
```

---
### Explanation of example

- this decorator takes the greet function as an argument
- it returns a new function (wrapper) that first prints a message, calls greet() and then prints another message

- @decorator syntax is a shorthand for greet = decorator(greet)

---
### Decorator with Parameters

Decorators often need to work with functions that have arguments
-  use *args and **kwargs so wrapper can accept any number of arguments

Example:
```
def decorator_name(func):
    def wrapper(*args, **kwargs):
        print("Before execution")
        result = func(*args, **kwargs)
        print("After execution")
        return result
    return wrapper
​
@decorator_name
def add(a, b):
    return a + b
​
print(add(5, 3))
```
```
Output
Before execution
After execution
8
```

---
### Explanation:

- decorator_name(func) is the decorator function 
- it takes another function (func) as input
- wrapper(*args, **kwargs) nested function that wraps func
- *args collects positional arguments, **kwargs collects keyword arguments

- @decorator_name equivalent to writing add = decorator_name(add) after the function definition

---
### Types of Decorators

1. Function Decorators
    - used to wrap and enhance functions 
2. Method Decorators
    - special decorators used for methods inside a class
    - they work like function decorators but handle the self parameter for instance methods
3. Class Decorators
    - used to modify or enhance behavior of a class
    - they work by taking class as an argument and returning a modified version of class

---
### Example Method Decorator

Example decorator that prints a message before and after a method is executed, while correctly handling self argument

```
def method_decorator(func):
    def wrapper(self, *args, **kwargs):
        print("Before method execution")
        res = func(self, *args, **kwargs)
        print("After method execution")
        return res
    return wrapper
​
class MyClass:
    @method_decorator
    def say_hello(self):
        print("Hello!")
obj = MyClass()
obj.say_hello()

Output
Before method execution
Hello!
After method execution
```

---
### Example Class Decorator

This code demonstrates a class decorator that adds a class_name attribute to a class, storing class’s name

```
def fun(cls):
    cls.class_name = cls.__name__
    return cls
​
@fun
class Person:
    pass
print(Person.class_name)

Output
Person
```

---
### Built-in Decorators

1. @staticmethod
    - use to define a method that doesn't operate on an instance of class (i.e., it doesn't use self). - - static methods are called on class itself, not on an instance of class
2. @classmethod: 
    - used to define a method that operates on class itself (i.e., it uses cls). Class methods can access and modify class state that applies across all instances of class.
3. @property: 
    - used to define a method as a property, which allows to access it like an attribute
    - this is useful for encapsulating implementation of a method while still providing a simple interface


---
### Example @staticmethod inside a class

This example shows how to define and use a @staticmethod inside a class

```
class MathOperations:
    @staticmethod
    def add(x, y):
        return x + y
​
res = MathOperations.add(5, 3)
print(res)

Output
8
```

---
### Example @classmethod 

This code defines a class Employee with a class variable raise_amount and a class method set_raise_amount that updates this variable for entire class

```
class Employee:
    raise_amount = 1.05
    def __init__(self, name, salary):
        self.name = name
        self.salary = salary
        
    @classmethod
    def set_raise_amount(cls, amount):
        cls.raise_amount = amount
​
Employee.set_raise_amount(1.10)
print(Employee.raise_amount)

Output
1.1
```

---
### Example @property

This code defines a circle class demonstrating @property for controlled attribute access, allowing safe updates to radius

```
class Circle:
    def __init__(self, radius):
        self._radius = radius
​
    @property
    def radius(self):
        return self._radius
​
    @radius.setter
    def radius(self, value):
        if value >= 0:
            self._radius = value
        else:
            raise ValueError("Radius cannot be negative")
​
    @property
    def area(self):
        return 3.14159 * (self._radius ** 2)
​
c = Circle(5)
print(c.radius) 
print(c.area)    
c.radius = 10
print(c.area)

Output
5
78.53975
314.159
```

---
### Class method vs Static Method
The key difference between a class method and a static method is whether the method needs access to the class itself


| Feature	| Class Method	| Static Method |
|-----------|---------------|---------------|
| Decorator Used|Defined using the @classmethod decorator|Defined using the @staticmethod decorator|
|First Parameter|Receives the class as the first parameter, conventionally named cls|Does not receive any automatic first parameter like self or cls|
|Access to Class Data|Can access and modify class-level variables because it has access to cls|Cannot access or modify class-level variables unless explicitly passed|
|Access to Instance Data|Cannot directly access instance variables unless an object is passed manually|Cannot access instance variables unless they are explicitly passed as arguments|
|Purpose|Commonly used to create factory methods or alternative constructors that return class objects|Typically used to define utility functions that logically belong to the class but do not depend on class or instance data|
|Object Creation|Can create or modify class instances using cls|Does not create or modify class instances automatically|

---
### Chaining Multiple Decorators

Chaining decorators means applying multiple decorators to same function. Each decorator wraps function in sequence, adding layered behavior

```
def decor1(func): 
    def inner(): 
        x = func() 
        return x * x 
    return inner 
​
def decor(func): 
    def inner(): 
        x = func() 
        return 2 * x 
    return inner 
​
@decor1
@decor
def num(): 
    return 10
​
@decor
@decor1
def num2():
    return 10
  
print(num()) 
print(num2())

Output
400
200
```

---
### Explanation

- in num(), decor runs first -> 10 becomes 20, then decor1 squares it -> 400
- in num2(), decor1 runs first -> 10 becomes 100, then decor doubles it -> 200

---
### Application of Decorators

- Logging: Track function calls (e.g., @logger)
- Authentication: Restrict access in web apps (e.g., Flask/Django)
- Rate Limiting: Control API usage per user
- Caching: Store results using functools.lru_cache
- Retry Logic: Automatically retry failed network calls
- Dependency Injection: Automatically inject contexts (FastAPI)
- Adding Metadata: Adding more contextual information to functions/methods/classes/properties

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Decorators

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Decorators