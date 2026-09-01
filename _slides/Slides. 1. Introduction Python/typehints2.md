### Python Types Intro

---
### Python Types
Python has support for optional "type hints" (also called "type annotations")

- allows declaring the type of a variable.

By declaring types for your variables, editors and tools can give you better support.

FastAPI is all based on these type hints, they give it many advantages and benefits.

---
### Example

```
Python 3.10+

def get_full_name(first_name, last_name):
    full_name = first_name.title() + " " + last_name.title()
    return full_name


print(get_full_name("john", "doe"))
```

Calling this program outputs:
'''
John Doe
'''

Python 3.10+

---
### Without typyings

Without typings you get no: 
- auto-complete
- error checking

---
### Add types

Let's modify a single line from the previous version.

```
Python 3.10+

def get_full_name(first_name: str, last_name: str):
    full_name = first_name.title() + " " + last_name.title()
    return full_name


print(get_full_name("john", "doe"))
```

Now we do get auto complete!

---
### More motivation
Check this function, it already has type hints:

```
Python 3.10+

def get_name_with_age(name: str, age: int):
    name_with_age = name + " is this old: " + age. <= ERROR HERE
    return name_with_age
```

Because the editor knows the types of the variables, you don't only get completion, you also get error checks:

Now you know that you have to fix it, convert age to a string with str(age):

```
Python 3.10+

def get_name_with_age(name: str, age: int):
    name_with_age = name + " is this old: " + str(age)
    return name_with_age
```

---
### Simple types
You can declare all the standard Python types, not only str.

You can use, for example:
- int
- float
- bool
- bytes

```
Python 3.10+

def get_items(item_a: str, item_b: int, item_c: float, item_d: bool, item_e: bytes):
    return item_a, item_b, item_c, item_d, item_e
```

---
### typing module
There are lots of other useable types in the typing module

```
from typing import Any


def some_function(data: Any):
    print(data)
```

Acutally Any turns of the type checking completely, dont use it!

---
### Generic types

Some types can take "type parameters" in square brackets, to define their internal types

```
# list of strings
list[str].   
```

These types that can take type parameters are called Generic types or Generics.

---
### Generic types (2)
The same goes for
- tuple
- set
- dict

---
### Tuple and Set

Lets look at a Tuple:

```
Python 3.10+

def process_items(items_t: tuple[int, int, str], items_s: set[bytes]):
    return items_t, items_s
```

This means:
- The variable items_t is a tuple with 3 items, an int, another int, and a str
- The variable items_s is a set, and each of its items is of type bytes

---
### Dict
To define a dict, you pass 2 type parameters, separated by commas:
```
Python 3.10+

def process_items(prices: dict[str, float]):
    for item_name, item_price in prices.items():
        print(item_name)
        print(item_price)
```

This means:
- The variable prices is a dict:
- The keys of this dict are of type str (let's say, the name of each item).
- The values of this dict are of type float (let's say, the price of each item)

---
### Union
You can declare that a variable can be any of several types, for example, an int or a str.

```
def process_item(item: int | str):
    print(item)
```

This means that item could be an int or a str.

---
### Possibly None
You can declare that a value could have a type, like str, but that it could also be None.

```
Python 3.10+

def say_hi(name: str | None = None):
    if name is not None:
        print(f"Hey {name}!")
    else:
        print("Hello World")
```

Using str | None instead of just str will let the editor help you detect errors where you could be assuming that a value is always a str, when it could actually be None too.

---
### Classes as types
You can also declare a class as the type of a variable.

Let's say you have a class Person, with a name:

```
Python 3.10+

class Person:
    def __init__(self, name: str):
        self.name = name


def get_person_name(one_person: Person):
    return one_person.name
```

Again, you get all the editor support:

Notice that this means "one_person is an instance of the class Person".

It doesn't mean "one_person is the class called Person".


