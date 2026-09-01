

# exercise 1. Add typings to this calculator class and its methods. 

class Calculator:
    def __init__(self, name:str | None = None):
        self.name = name or "Calculator"

    def add(self, a:int, b:int) -> int:
        return a + b

    def subtract(self, a:int, b:int) -> int:
        return a - b

    def divide(self, a:int, b:int) -> float | None:
        if b == 0:
            return None
        return a / b

    def multiply(self, a:int, b:int) -> int:
        return a * b

def createCalculator() -> Calculator:
    return Calculator()


answer:int = createCalculator().add(5, 10)
print(f"Answer: {answer}")