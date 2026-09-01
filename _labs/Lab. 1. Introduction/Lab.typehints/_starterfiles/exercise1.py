

# exercise 1. Add typings to this calculator class and its methods. 

class Calculator:
    def __init__(self, name = None):
        self.name = name or "Calculator"

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def divide(self, a, b):
        if b == 0:
            return None
        return a / b

    def multiply(self, a, b):
        return a * b

def createCalculator():
    return Calculator()


answer = createCalculator().add(5, 10)
print(f"Answer: {answer}")