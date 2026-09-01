# Generators 

---
### Generators 

*Generators in Python are specialized functions that produce a stream of values lazily—one item at a time on demand, rather than computing a full dataset and storing it entirely in memory*

---
### Yields 

When Python hits a yield statement
- it returns the current value and pauses execution
- preserve the function's entire internal state (local variables, execution line, and environment)

When the generator is asked for the next() or inside a for loop, it execution resumes immediately after the yield line.

```
def countdown(n):
    while n > 0:
        yield n
        n -= 1

gen = countdown(3)

print(next(gen))  # Output: 3
print(next(gen))  # Output: 2
print(next(gen))  # Output: 3rd value (1)

# The next call raises StopIteration to signal completion
```

---
### Next

next() is a globally available built-in Python function (located in the builtins module, requiring no import statements) that retrieves the next item from an iterator object

---
### How Next Works

Under the hood, next(iterator) invokes the iterator's internal __next__() dunder method

It advances the iterator's state by one step and returns the produced value

Mechanics
- iteration Step => returns the immediate next item from an active stream or sequence
- exhaustion Handling => raises a StopIteration exception when the iterator runs out of items
- default Fallback => accepts an optional second argument—next(iterator, default)
    - which returns a fallback value instead of raising StopIteration 

---
### Code Example

```
# Create an iterator from a list
colors = iter(["red", "blue"])

# Advance through items manually
print(next(colors))  # Output: red
print(next(colors))  # Output: blue

# Safe handling with a default value once exhausted:
print(next(colors, "No more colors"))  # Output: No more colors

# Without a default value, an exhausted iterator raises an error:
print(next(colors))  # Rai
```

---
### Key Advantages of Generators

- Memory Efficiency
 - standard collections construct the entire dataset upfront (O(N) memory)
 - generators evaluate items dynamically (O(1) memory), ideal for reading large log files, processing database streams, or generating infinite sequences
- Simplified State Management
    - automatically handles state, iteration, and termination protocols without requiring custom __iter__() and __next__() in a class
- Pipeline Processing
    - allows chaining multiple generator expressions together cleanly without building intermediate temporary lists

---
### Generator Expressions
For shorter tasks, Python offers generator expressions 

They share the same compact syntax as list comprehensions but use parentheses () instead of square brackets []

```
# Creates a full 1,000,000-item list in memory:
list_comp = [x ** 2 for x in range(1000000)]

# Creates an iteration object using almost zero memory:
gen_exp = (x ** 2 for x in range(1000000))

# Consumes values lazily:
print(sum(gen_exp))
```

---
### Generators and Type Hints

Type hinting Python generators relies on collections.abc.Generator for explicit control over yield, send, and return types, or collections.abc.Iterator for simpler yield-only streams

---
### The Complete Signature: Generator

When using collections.abc.Generator the hint takes three parameters: Generator[YieldType, SendType, ReturnType]

- YieldType: The data type produced by yield
- SendType: The data type received when passing data back in via .send(value) 
    - if you do not use .send(), set this to None
- ReturnType: The data type returned upon completion via return value (which sets StopIteration.value). 
    - if there is no explicit return, set this to None

---
### Simplified Hints: Iterator vs. Iterable

Because most generators only yield values, writing Generator[int, None, None] can become needlessly verbose

Use
- Iterator[T]: The standard, clean return annotation for simple generators that only yield items of type T
- Iterable[T]: Recommended for function arguments when your function can accept any collection or generator, rather than for the return hint of the generator itself.

---
### Code Examples

Standard Generator (Yield-Only)

```
from collections.abc import Iterable, Iterator

# INPUT: Use Iterable so the function accepts lists, tuples, or generators
def process_data(items: Iterable[int]) -> int:
    return sum(items)

# OUTPUT: Use Iterator as the clean shorthand for a generator function
def generate_squares(limit: int) -> Iterator[int]:
    for i in range(limit):
        yield i ** 2
```
---
### Code Examples

Advanced Generator (Yield, Send, and Return)
```
from collections.abc import Generator

def running_accumulator() -> Generator[int, int, str]:
    total = 0
    while total < 100:
        # Yields total (int), receives added_val from .send() (int)
        added_val = yield total
        if added_val is not None:
            total += added_val
            
    # Returns final message (str) when loop breaks
    return "Target limit reached"

# Usage
gen = running_accumulator()
print(next(gen))      # Output: 0
print(gen.send(30))   # Output: 30
print(gen.send(80))   # Raises StopIteration: Target limit reached
```

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Generators

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Generators