
# exercise 3. Add generics to this calculator class and its methods. 


class Calculator[T: (int, float)]:
    def __init__(self, name = None):
        self.name = name or "Calculator"

    def add(self, a: T, b: T) -> T:
        return a + b

    def subtract(self, a: T, b: T) -> T:
        return a - b

    def divide(self, a: T, b: T) -> float | None:
        if b == 0:
            return None
        return a / b

    def multiply(self, a: T, b: T) -> T:
        return a * b

def createCalculator[T: (int, float)]() -> Calculator[T]:
    return Calculator[T]()