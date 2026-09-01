#exercise 4.1 Create two typed functions that take a list. 
# the first function should filter the list based on a condition and return a new list.
# the second function should transform the list based on a condition and return a new list.

from typing import Callable

def where[T](list: list[T], wherefunc: Callable[[T], bool]) -> list[T]:
    return [s for s in list if wherefunc(s)]

def select[T,R](list: list[T], selectfunc: Callable[[T], R]) -> list[R]:
    return [selectfunc(s) for s in list]    

# exercise 4.1.1 test the functions with a list of strings and a list of integers.
strings = ["john", "jane", "doe", "alice", "bob"]
filtered_strings = where(strings, lambda x: len(x) > 3)
transformed_strings = select(filtered_strings, lambda x: x.upper())

print("Exercise 4.1.1:")
print(filtered_strings)
print(transformed_strings)


# exercise 4.2 Create a Person class with name and age attributes and test your previously created functions with a list of Person objects.
# make sure to use the where function to filter the list of Person objects based on a condition and the select function to transform the list of Person objects to strings.

class Person:
    def __init__(self, name:str, age:int):
        self.name = name
        self.age = age

    def __repr__(self):
        return f"Person(name={self.name}, age={self.age})"

persons = [Person("john", 30), Person("jane", 25), Person("doe", 20), Person("alice", 35), Person("bob", 40)]
persons = where(persons,lambda x: len(x.name) > 3)
persons = select(persons, lambda x: x.name.upper())

print("Exercise 4.2:")
print(persons)


    
# exercise 4.3 Create a LINQ class that takes a list and has two methods: where and select. 
# Each method should take a function as an argument and return a new LINQ object with the filtered or transformed list.
# therefore we can use autocompletion to chain the methods together.
# Make sure to use correct typing for the class and its methods.

class LINQ[T]:
    def __init__(self, list:list[T]):
        self.list = list

    def where(self, wherefunc: Callable[[T], bool]) -> 'LINQ[T]':
        return LINQ([s for s in self.list if wherefunc(s)])

    def select[R](self, selectfunc: Callable[[T], R]) -> 'LINQ[R]':
        return LINQ([selectfunc(s) for s in self.list])

    def __repr__(self):
        return f"{self.list}"
    
# test the LINQ class with the Person class
persons = LINQ(["john", "jane", "doe", "alice", "bob"]).where(lambda x: len(x) > 3).select(lambda x: Person(x, len(x) * 10))

print("Exercise 4.3:")
print(persons)