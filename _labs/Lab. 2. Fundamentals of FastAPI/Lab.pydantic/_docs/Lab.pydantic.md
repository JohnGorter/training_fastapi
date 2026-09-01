## Lab Pydantic
In this lab you will learn the basics about Pydantic. You wil create, validate, serialize and deseralize a model with different validation logic. 
> duration: 20 minutes

### Step 1. Create a new project in a working folder for your labs
Navigate to your lab folder and create a new project with uv, name it lab_pydantic. 

```
uv init --no-package lab_pydantic
```

Navigate to the just created folder
```
cd ./lab_pydantic
```

Dont forget to add packages Pydantic and Pydantic[[email]]to your project using uv add. You dont have to use FastAPI now!


commands
```
uv add pydantic
uv add "pydantic[email]"
```

Make sure the project is created without package (--no-package) and the main.py is empty. 

### Step 2. Write your first real life Pydantic model
Open the main.py and write a User class that inherits from BaseModel. 

Make sure you meet the following requirements
- the fields are firstname, lastname, password, email and created_at
- the firstname has to be more than 2 characters and max 50 characters
- the firstname can not contain anything other than letters
- the lastname has to be more than 2 characters and max 50 characters
- the lastname can not contain anything other than letters
- the password has to be more than 6 characters and should contain at least a digit and a uppercase character
- the email field has to be an email field, but is optional
- the created_at should me automatically filled with the exact datetime the instantiation of the object itself

To give you a heads start, here is the definition of the object and the code to validate the workings. You only have to implement the correct definitions.

```
class User(BaseModel):
    # your code here
    pass

print("User model defined successfully")
try:
    user = User(
        firstname="John",
        lastname="Doe",
        password="Password1",
        email="john@test.nl"
    )
    print(user.model_dump())
except ValidationError as e:
    print(e)

```

Run the code using
```
uv run ./main.py
```
and make sure that no errors occur and the output reflects a correct model. 

### Step 3. Add complexity

In the User definition, there is no Address yet. Change the code and add Adress (Street, Postalcode, City, Country and HouseNumber) data to the user object. 

The requirements for the address class are
- street is a string of minimal 1 and maximal 100 characters
- city is a string of minimal 1 and maximal 50 characters
- state is a string of exact 2 characters
- zip_code is a dutch zip code containing of 4 digits and 2 letters possible with a space between the digits and letter-pair (use a pattern/regex for this field)
- country is a string of minimal 1 and maximal 50 characters

Add two addresses to the user for the shipping and the billing attribute of the user: 
- shippingaddres
- billingaddress (optional)

As you can see from the definition, the billingaddress is optional. Make sure this requirement is met. 

To give you a start, copy the following boilerplate code and make your adjustments on the marked spots in the code.

```
class Address(BaseModel):
    # your code here
    pass


class User(BaseModel):
    firstname: str = Field(..., min_length=2, max_length=50)
    lastname: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None

    # your code here

    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator('password')
    @classmethod
    def validate_password(cls, value):
        if not any(char.isdigit() for char in value):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in value):
            raise ValueError('Password must contain at least one uppercase letter')
        return value

print("User model defined successfully")

try:
    user = User(
        firstname="John",
        lastname="Doe",
        password="Password1",
        email="john@test.nl",

        shipping_address={
            "street": "kerkstraat 1",
            "city": "Amsterdam",
            "state": "NH",
            "zip_code": "1234 AB",
            "country": "Netherlands"
        },
    )
    print(user.model_dump())
except ValidationError as e:
    print(e)

```

Run the code using
```
uv run ./main.py
```
and make sure that no errors occur and the output reflects a correct model. 

### Extra Exercise
Write some code to test if invalid user or address data result in correct validation errors. Think of leaving out the shipping address, supplying invalid postal codes, email or passwords, exceeding the limits of the state field in the address etc.

Perhaps you can think of some more violations yourself!

### Summary
We have defined simple and complexer Pydantic models for a real life example of user objects. This was an introduction to Pydantic, you are now ready to use it in FastAPI!

Congrats!

-= End of lab =-
  
