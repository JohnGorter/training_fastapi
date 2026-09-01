# Advanced TypeHints

---
### TypeVar
TypeVar is used to define a type variable. This is useful when you want to enforce the same type across multiple parts of a function or class.

```
from typing import List, TypeVar

T = TypeVar('T')


def first_and_last(items: List[T]) -> T:
    return items[0]
```

result = first_and_last([1, 2, 3, 4])  # result: int
Type
Type is used to indicate that something is a class rather than an instance of a class.

from typing import Type


class Animal:
    @classmethod
    def make_sound(cls):
        pass


def mimic(animal_class: Type[Animal]):  # animal_class is a class, not an instance
    animal_class.make_sound()


mimic(Animal)
TypedDict
TypedDict is a powerful tool in the typing module that allows you to specify types for individual keys in dictionaries. This is especially useful when dealing with data structures like JSON, where you want to ensure a specific structure for your dictionaries.

from typing import TypedDict


class Person(TypedDict):
    name: str
    age: int


# This is valid
person1: Person = {"name": "Alice", "age": 30}

# This would raise a type error
person2: Person = {"name": "Bob", "age": "thirty"}  # 'age' is expected to be an int
By default, all keys in a TypedDict are required. However, you can specify optional keys using the total keyword argument:

from typing import TypedDict


class OptionalPerson(TypedDict, total=False):
    name: str
    age: int


# This is valid even without the 'age' key
person1: OptionalPerson = {"name": "Charlie"}
TypeAlias
A TypeAlias is a way to provide a new name for an existing type, often to simplify complex type annotations or to provide more context about the type's purpose.

You can create a TypeAlias by simply assigning a type to a variable:

from typing import List, Dict

# Using TypeAlias for better readability
Matrix = List[List[int]]
PersonData = Dict[str, Union[str, int, float]]


# This is now a valid type annotation
def determinant(m: Matrix) -> float:
    # Implementation here...
    pass
TypeGuard
TypeGuard is a way to narrow down types using custom functions. It's useful in situations where the type checker can't determine the type on its own.

A function that returns TypeGuard[T] is essentially telling the type checker: "If this function returns True, then the variable you passed in is of type T."

from typing import Any, TypeGuard


def is_integer(value: Any) -> TypeGuard[int]:
    return isinstance(value, int)
In the above example, if is_integer returns True, the type checker knows that value is an int.

Here’s how you might use a TypeGuard in a real-world scenario:

from typing import List, Union, TypeGuard


def is_string_list(values: List[Union[int, str]]) -> TypeGuard[List[str]]:
    return all(isinstance(value, str) for value in values)


def process(values: List[Union[int, str]]):
    if is_string_list(values):
        # Within this block, 'values' is treated as List[str] by the type checker
        concatenated = " ".join(values)
        print(concatenated)
    else:
        # Here, 'values' is still List[Union[int, str]]
        print("List contains non-string values.")
It’s important to note that TypeGuard only influences static type checkers. It doesn't have any impact on the actual runtime behavior of the code.
The function returning TypeGuard[T] should not have any side effects. It should only perform checks and return a boolean value.
Generic
Generics are a feature that allows you to define classes, functions, and data structures that can operate on typed parameters. This promotes code reusability while maintaining type safety.

You can define a generic class using Generic[T], where T is a type variable:

from typing import Generic, TypeVar

T = TypeVar('T')


class Box(Generic[T]):
    def __init__(self, item: T):
        self.item = item


class Container(Generic[T]):
    def __init__(self, value: T):
        self.value = value


box_int = Box(5)  # box_int: Box[int], class Box(item: int)
box_str = Box("Hello")  # box_str: Box[str], class Box(item: str)

# This allows for type-safe operations on the container
int_container = Container[int](5)
str_container = Container[str]("Hello")
Functions can also be generic, allowing them to operate on different types while preserving type information:

def reverse_content(container: Container[T]) -> Container[T]:
    reversed_content = container.value[::-1]
    return Container(reversed_content)


reversed_str_container = reverse_content(str_container)  # Contains "olleH"
You can place constraints on type variables to limit the types they can represent:

U = TypeVar('U', int, float)


class NumericContainer(Generic[U]):
    pass


# This is valid
numeric_container = NumericContainer[int](10)

# This would raise a type error
string_container = NumericContainer[str]("Invalid")
Conclusion
Python’s type hinting system, introduced in recent versions, has revolutionized the way developers write and understand code. With tools like Generic, TypeVar, Type, TypedDict, TypeAlias, and TypeGuard, the typing module offers a rich set of utilities that cater to both basic and advanced use cases. These tools not only enhance code readability but also ensure robustness by catching potential type errors during static type checking.

As developers, embracing these advanced type annotations can lead to fewer runtime errors, clearer code documentation, and an overall improved coding experience. Whether you’re a seasoned Pythonista or just starting your journey, understanding and incorporating these type annotations can elevate the quality of your code. As Python continues to evolve, it’s exciting to think about the future possibilities and enhancements in the realm of type hinting.
---
### What are Type Hints

*Type hints in Python are a major step towards combining the **flexibility of a dynamically typed language** with the clarity of a **statically typed language**.*

*They serve as a form of documentation that allows developers to explicitly state the expected data types of function arguments and return values.*



---
### Why Use Type Hints?

- Improved Code Readability: Makes it easier to understand what type of data each function expects and returns.
- Facilitates Debugging: Helps in identifying type-related errors.
- Enhanced Development Experience: IDEs use type hints for better code completion and error detection.
- Static Type Checking: Tools like mypy can use type hints to perform static type checking.

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
### Using Type Hints in Classes
Type hints are extremely useful in object-oriented programming, namely for class attributes and methods:

- Attributes: attr: type
- Methods: Similar to functions.

---
### Exampe

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
### Type Hints for Dynamic and Complex Situations
Type hints are versatile and can handle complex coding scenarios:
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
### Best Practices for Using Type Hints
- Be Consistent: Apply type hints throughout your codebase
- Use Them for Documentation: They should aid in understanding the code, not complicate it
- Avoid Over-Complication: Keep type hints simple and readable
- Stay Updated: Keep abreast of changes and improvements in Python's typing system

---
### Common Pitfalls and Misconceptions

- Misunderstanding None Types: Remember to use Optional for functions that might return None!
- Confusing Type Hints with Type Enforcement: Type hints are not enforced at runtime!
- Overusing Any: Using Any too frequently defeats the purpose of type hints!


---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Type Hints



---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Animations

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
