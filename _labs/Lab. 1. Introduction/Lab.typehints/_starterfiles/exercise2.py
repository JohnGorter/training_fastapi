# exercise 4.1 Create two typed functions that take a list. 
# the first function should filter the list based on a condition and return a new list.
# the second function should transform the list based on a condition and return a new list.

from typing import Callable

# 1. ... your code goes here ...

# exercise 4.1.1 test the functions with a list of strings and a list of integers.

strings = ["john", "jane", "doe", "alice", "bob"]

# 2. ... your code goes here ...

print("Exercise 4.1.1:")
print(filtered_strings)
print(transformed_strings)


# exercise 4.2 Create a Person class with name and age attributes and test your previously created functions with a list of Person objects.
# make sure to use the where function to filter the list of Person objects based on a condition and the select function to transform the list of Person objects to strings.

# 3. ... your code goes here ...

print("Exercise 4.2:")
print(persons)

    
# exercise 4.3 Create a LINQ class that takes a list and has two methods: where and select. 
# Each method should take a function as an argument and return a new LINQ object with the filtered or transformed list.
# therefore we can use autocompletion to chain the methods together.
# Make sure to use correct typing for the class and its methods.

# 4. ... your code goes here ...
# hint the class should be something like this but then more generic and with correct typing for the methods: 
# class LINQ:
#    def __init__(self, list):
#        self.list = list
#
#    def where(self, wherefunc):
#        return LINQ([s for s in self.list if wherefunc(s)])
#
#    def select[R](self, selectfunc):
#        return LINQ([selectfunc(s) for s in self.list])
#
#   def __repr__(self):
#       return f"{self.list}"    


# Exercise 4.3.1 test the LINQ class with the Person class where you create a LINQ object with a list of strings and then use the where method to filter the list based on a 
# condition and the select method to transform the list to a list of Person objects.
# The condition for the where method should be that the length of the string is greater than 3 and the select method should 
# create a Person object with the name being the string and the age being the length of the string multiplied by 10.

# 5. ... your code goes here ...    

print("Exercise 4.3:")
print(persons)