# TypeHints

---
### What are Type Hints

*Type hints in Python are a major step towards combining the **flexibility of a dynamically typed language** with the clarity of a **statically typed language**.*

*They serve as a form of documentation*



---
### Why Use Type Hints?

- Improved Code Readability
    - easier to understand what type of data each function expects and returns
- Facilitates Debugging
    - helps in identifying type-related errors
- Enhanced Development Experience
    - IDEs use type hints for better code completion and error detection
- Static Type Checking
    - Tools like mypy can use type hints to perform static type checking.

---
### How to operate

To check your code, you have to run mypy:
```
mypy main.py
```

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Type hint basics

---
### Basic Annotations

- Variables: variable_name: type = value
- Functions:
  - Parameters: def function_name(param1: type, param2: type) -> return_type

  *Return Type: Indicated after the -> symbol*

---
###  Example

```
def add_numbers(a: int, b: int) -> int:
    return a + b
```

---
### Complex Types
Lists, Tuples, and Sets:

```
from typing import List, Tuple, Set
def process_values(values: List[int]) -> Set[str]:
```

---
### Refresher 

What is the difference between Lists, Tupels and Sets in Python?

---
### List

A List is a collection of ordered, mutable elements that can hold a variety of data types. 

Key Characteristics:
- Mutable: Elements can be modified after creation
- Ordered: Maintains the order of elements
- Allows Duplicates: Can have multiple occurrences of the same value
- Heterogeneous: Can store different data types

---
### List Example


```
# Creating a List
a = [1, 2, 3, 'Python', 3]
​
# Accessing elements by indexing
print(a[0]) 
print(a[-1]) 
​
# Modifying an element
a[1] = 'Updated'
print(a)  
​
# Appending an element
a.append(4)
​
# Removing an element
a.remove(3)
​
# List slicing
print(a[1:3])

Output
1
3
[1, 'Updated', 3, 'Python', 3]
['Updated', 'Python']
```

---
### Sets

A Set is an unordered collection of unique elements. Sets are primarily used when membership tests and eliminating duplicate values are needed

Key Characteristics:
- Mutable: Elements can be added or removed
- Unordered: Does not maintain the order of elements
- Unique Elements: Duplicate values are automatically removed
- Heterogeneous: Can store different data types

---
### Sets Example

```
# Creating a Set
s = {1, 2, 3, 'Python', 3}
print(s) 
​
# Adding elements
s.add(4)
​
# Removing elements
s.remove(3)  # KeyError if the element is not present
​
# Accessing elements (No indexing because it is unordered)
# for element in s:
#     print(element)

Output
{'Python', 1, 2, 3}
```

---
### Tuples

A Tuple is an ordered, immutable collection of elements. Tuples are often used when data should not be modified after creation

Key Characteristics:
- Immutable: Once created, elements cannot be modified.
- Ordered: Maintains the order of elements.
- Allows Duplicates: Can contain duplicate values.
- Heterogeneous: Can store different data types.

---
### Tupels Example

```
# Creating a Tuple
tup = (1, 2, 3, 'Python', 3)
​
# Accessing elements by indexing
print(tup[0])
print(tup[-1])
​
# Tuple slicing
print(tup[1:4])
​
# Attempting to modify a tuple (Raises TypeError)
# tup[1] = 'Updated'  # Uncommenting this will raise an error

Output
1
3
(2, 3, 'Python')
```

---
### Use Cases

Use lists => when frequent modifications are required

Use Sets => when uniqueness is needed

Use Tupels => when immutability is required


---
### Dictionaries

```
from typing import Dict
def count_frequency(words: List[str]) -> Dict[str, int]:
```

---
### Optional Types and Union Types

Optional Types 
```
from typing import Optional
```
Union Types 
```
from typing import Union
```

---
### Example

```
from typing import Optional, Union

def find_item(items: List[str], query: str) -> Optional[Union[str, int]]:
    # Implementation
```

---
### Example in newer syntax

Since Python 3.10, we can use cleaner syntax

```
def find_item(items: List[str], query: str) -> str | int | None:
    # Implementation
```


---
### Using Type Hints in Classes
Type hints are extremely useful in object-oriented programming, namely for class attributes and methods

- Attributes: attr: type
- Methods: Similar to functions

---
### Example

```
class Person:
    name: str
    age: int

    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age

    def greet(self) -> str:
        return f"Hello, my name is {self.name}"
```

---
### Any

Any type is dynamically typed 

Mypy doesn’t know anything about the possible runtime types of such value
- any operations are permitted on the value
- the operations are only checked at runtime
- use Any as an “escape hatch” when you can’t use a more precise type for some reason

---
### Example 

```
a: Any = None
s: str = ''
a = 2     # OK (assign "int" to "Any")
s = a     # OK (assign "Any" to "str")
```

** Be careful with Any types, since they let you lie to mypy, and this could easily hide bugs**

---
### Type Hints for Dynamic and Complex Situations

Type hints are versatile and can handle complex coding scenarios
- Generics: from typing import Generic, TypeVar
- Callable: from typing import Callable

---
### Example

```
T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value
```
```
def execute_function(func: Callable[[int], str], value: int) -> str:
    return func(value)
```

---
### Newer Syntax, Again

Since Python 3.12 and newer, you can use better syntax!

```
class Container[T]:
    def __init__(self, value: T) -> None:
        self.value = value
```
```
def execute_function[T](func: Callable[[int], T], value: int) -> T:
    return func(value)
```

---
### Generic bound and contstrained

In the case below, the type is either:
- int
- float
- int | float <- notice the mix here

```
class Calculator[T: int | float]:
    def addItems(item:T, item:T) -> None:
        pass
```

Someone can create Calculator[[int | float]]() and pass a mix of int and float arguments (e.g., add(5, 2.5))

---
### Generic bound and constrained

In the case below, the type is either:
- int
- float

```
class Container[T: (int, float)]:
    def addItems(item:T, item2:T) -> None:
        pass
```

Constrained ([T: (int, float)]): Forces T to be strictly int or strictly float. It forbids mixing int and float in the same calculator instance!

---
### Returning your own type

In the case a function in the class should return a new instance of that class, you cant do this:
```
class Calculator[T: (int, float)]:
    def __init__(self, sum:T):
        self.sum:T = sum
    def add(self, a:T) -> Calculator[T]:     <-- Error Calculator is not defined
        self.sum = self.sum + a;
        return Calculator(self.sum)

```

---
### Returning your own type (2)

Fix this by adding quotes to the type:
```
class Calculator[T: (int, float)]:
    def __init__(self, sum:T):
        self.sum:T = sum
    def add(self, a:T) -> 'Calculator[T]':     
        self.sum = self.sum + a;
        return Calculator(self.sum)

```


---
### Best Practices for Using Type Hints
- Be Consistent
    - apply type hints throughout whole codebase
- Use Them for Documentation
    - they should aid in understanding the code, not complicate it
- Avoid Over-Complication
    - keep type hints simple and readable
- Stay Updated
    - keep abreast of changes and improvements in Python's typing system

---
### Common Pitfalls and Misconceptions

- Misunderstanding None Types
    - remember to use Optional or None for functions that might return None!
- Confusing Type Hints with Type Enforcement
    - type hints are not enforced at runtime!
- Overusing Any
    - using Any too frequently defeats the purpose of type hints!


---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Type Hints

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Typehints
