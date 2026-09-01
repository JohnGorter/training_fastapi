
from pydantic import BaseModel, Field, EmailStr, model_validator, field_validator, ValidationError
from typing import Optional
from decimal import Decimal
from datetime import datetime
from typing import List


class Address(BaseModel):
    street: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=50)
    state: str = Field(..., min_length=2, max_length=2) 
    # use the dutch postalcode format
    zip_code: str = Field(..., pattern=r'^[1-9][0-9]{3}\s?[a-zA-Z]{2}$')
    country: str = Field(..., min_length=1, max_length=50)


class User(BaseModel):
    firstname: str = Field(..., min_length=2, max_length=50)
    lastname: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None

    shipping_address: Address = Field(..., description="The shipping address of the user")
    billing_address: Optional[Address] = Field(None, description="The billing address of the user, if different from the shipping address")

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

