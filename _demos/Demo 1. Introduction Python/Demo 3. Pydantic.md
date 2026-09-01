
step 1: create a new uv project, name it demo_pydantic (use --no-package)
step 1: install pydantic using: uv add pydantic
step 2: add the following code to the main.py file:
    ```
    from pydantic import BaseModel

    class Person(BaseModel):
        name: str
        age: int
        email: str

    data = {
        "name": "John Doe",
        "age": 30,
        "email": "john.do@example.com"
    }

    PersonInstance = Person(**data)
    print(PersonInstance)

    ```
step 3: run this code using uv run ./main.py and check to see that it all went fine!
step 4: change the code so we have a validation error!
```
    from pydantic import BaseModel, ValidationError

    class Person(BaseModel):
        name: str
        age: int
        email: str

    data = {
        "name": 1,
        "age": "thirty",
        "email": "john.do@example.com"
    }

    try:
        PersonInstance = Person(**data)
        print(PersonInstance)
    except ValidationError as e:
        print(f"Error: {e}")    

```

step 5; show the error that occurs when you run this code.
step 6: fix the code and rerun the code again to show that everything works fine!
step 7: add email validation to the project though: uv add "pydantic[email]"
step 8: change the code to include email validation
```
    from pydantic import BaseModel, ValidationError, EmailStr


    class Person(BaseModel):
        name: str
        age: int
        email: EmailStr

    data = {
        "name": "John Doe",
        "age": 30,
        "email": "john.do@example.com"
    }

    try:
        PersonInstance = Person(**data)
        print(PersonInstance)
    except ValidationError as e:
        print(f"Error: {e}")    

```
step 9: check and run the code, change the email and remove the @ sign, run it again, notice that the email validation works!
