
from pydantic import BaseModel, Field, EmailStr, model_validator, field_validator, ValidationError
from typing import Optional
from decimal import Decimal
from datetime import datetime
from typing import List

# demo 1. Pydantic model validation and conversion
class User(BaseModel):
   age: int
   email: EmailStr
   is_active: bool = True
   nickname: Optional[str] = None

# Pydantic automatically validates and converts data
user_data = {
   "age": "25",  # String gets converted to int
   "email": "john@example.com",
   "is_active": "true"  # String gets converted to bool
}

# demo 2. invalid data handling
user = User(**user_data)
print(user.age)  # 25 (as integer)
print(user.model_dump())  # Clean dictionary output

try:
   invalid_user = User(
       name="",  # Empty string
       email="not-an-email",  # Invalid email
       age=-5  # Negative age
   )
except ValidationError as e:
   print(e)


# demo 3. complexer validation
class Product(BaseModel):
   name: str = Field(min_length=1, max_length=100)
   price: Decimal = Field(gt=0, le=10000)  # Greater than 0, less than or equal to 10,000
   description: Optional[str] = Field(None, max_length=500)
   category: str = Field(..., pattern=r'^[A-Za-z\s]+$')  # Only letters and spaces
   stock_quantity: int = Field(ge=0)  # Greater than or equal to 0
   is_available: bool = True

# This works - all constraints satisfied
valid_product = Product(
   name="Wireless Headphones",
   price="199.99",  # String converted to Decimal
   description="High-quality wireless headphones",
   category="Electronics",
   stock_quantity=50
)

# This fails with clear error messages
try:
   invalid_product = Product(
       name="",  # Too short
       price=-50,  # Negative price
       category="Electronics123",  # Contains numbers
       stock_quantity=-5  # Negative stock
   )
except ValidationError as e:
   print(f"Validation errors: {len(e.errors())} issues found")

# demo 4. strictness demo
# Default: lenient type coercion
class FlexibleOrder(BaseModel):
   order_id: int
   total_amount: float
   is_paid: bool

# Strict validation when precision matters
class StrictOrder(BaseModel):
   model_config = {"str_strip_whitespace": True, "validate_assignment": True}

   order_id: int = Field(strict=True)
   total_amount: float = Field(strict=True)
   is_paid: bool = Field(strict=True)

# These all work due to automatic conversion
flexible_order = FlexibleOrder(
   order_id="12345",  # String to int
   total_amount="99.99",  # String to float
   is_paid="true"  # String to bool
)

# These all work due to automatic conversion
try: 
    strict_order = StrictOrder(
        order_id="12345",  # String to int
        total_amount="99.99",  # String to float
        is_paid="true"  # String to bool
    )
except ValidationError as e:
    print(f"Strict validation errors: {len(e.errors())} issues found")


# demo 5. nested models and lists
class Address(BaseModel):
   street: str = Field(min_length=5)
   city: str = Field(min_length=2)
   postal_code: str = Field(pattern=r'^\d{5}(-\d{4})?$')
   country: str = "USA"

class Customer(BaseModel):
   name: str = Field(min_length=1)
   email: EmailStr
   shipping_address: Address
   billing_address: Optional[Address] = None

class OrderItem(BaseModel):
   product_id: int = Field(gt=0)
   quantity: int = Field(gt=0, le=100)
   unit_price: Decimal = Field(gt=0)

class Order(BaseModel):
   order_id: str = Field(pattern=r'^ORD-\d{6}$')
   customer: Customer
   items: List[OrderItem] = Field(min_length=1)
   order_date: datetime = Field(default_factory=datetime.now)

# Complex nested data validation
order_data = {
   "order_id": "ORD-123456",
   "customer": {
       "name": "John Doe",
       "email": "john@example.com",
       "shipping_address": {
           "street": "123 Main Street",
           "city": "Anytown",
           "postal_code": "12345"
       }
   },
   "items": [
       {"product_id": 1, "quantity": 2, "unit_price": "29.99"},
       {"product_id": 2, "quantity": 1, "unit_price": "149.99"}
   ]
}

order = Order(**order_data)
print(f"Order validated with {len(order.items)} items")


# demo 6. field validator decorator
import re
class UserRegistration(BaseModel):
   username: str = Field(min_length=3)
   email: EmailStr
   password: str
   subscription_tier: str = Field(pattern=r'^(free|pro|enterprise)$')

   @field_validator('password')
   @classmethod
   def validate_password_complexity(cls, password, info):
       tier = info.data.get('subscription_tier', 'free')

       if len(password) < 8:
           raise ValueError('Password must be at least 8 characters')

       if tier == 'enterprise' and not re.search(r'[A-Z]', password):
           raise ValueError('Enterprise accounts require uppercase letters')

       return password

try:
    u = UserRegistration(
        username="johndoe",
        email="john@test.nl", 
        password="Pass123",
        subscription_tier="enterprise"
    )
    print(u.model_dump())
except ValidationError as e:
    print(f"Validation errors: {len(e.errors())} issues found")

# demo 7. model validator decorator
class EventRegistration(BaseModel):
   start_date: datetime
   end_date: datetime
   max_attendees: int = Field(gt=0)
   current_attendees: int = Field(ge=0)

   @model_validator(mode='after')
   def validate_event_constraints(self):
       if self.end_date <= self.start_date:
           raise ValueError('Event end date must be after start date')

       if self.current_attendees > self.max_attendees:
           raise ValueError('Current attendees cannot exceed maximum')

       return self

try:
   m = EventRegistration(
       start_date=datetime(2024, 6, 1, 10, 0),
       end_date=datetime(2024, 6, 1, 9, 0),  # Invalid: end before start
       max_attendees=100,
       current_attendees=50
   )
   print(m.model_dump())
except ValidationError as e:
   print(f"Validation errors: {len(e.errors())} issues found")