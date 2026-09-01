from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int


def main():
    print("Hello from pydantic!")


if __name__ == "__main__":
    main()
