# Pydantic 

---
### Why?
Instead of writing dozens of <code>if isinstance()</code> checks and custom validation functions, you define your data structure once using familiar Python syntax

Pydantic handles the rest:
- validating incoming data
- converting types when appropriate
- providing clear error messages when validation fails

---
### A Scenario

Consider this simple Python function with type hints and proper documentation

```
def calculate_user_discount(age: int, is_premium_member: bool, purchase_amount: float) -> float:
   """Calculate discount percentage based on user profile and purchase amount."""
   if age >= 65:
       base_discount = 0.15
   elif is_premium_member:
       base_discount = 0.10
   else:
       base_discount = 0.05
  
   return purchase_amount * base_discount

discount = calculate_user_discount(True, 1, 5)
print(discount)  # Output: 0.5 (True becomes 1, 1 is truthy, so 5 * 0.10)
```

This runs without error, even though types are completely wrong!

---
### Remeber these lines of code?

```
def create_user(data):
   # Manual validation nightmare
   if not isinstance(data.get('age'), int):
       raise ValueError("Age must be an integer")
   if data['age'] < 0 or data['age'] > 150:
       raise ValueError("Age must be between 0 and 150")
   if not isinstance(data.get('email'), str) or '@' not in data['email']:
       raise ValueError("Invalid email format")
   if not isinstance(data.get('is_active'), bool):
       raise ValueError("is_active must be a boolean")
  
   # Finally create the user...
   return User(data['age'], data['email'], data['is_active'])
```

Multiply this by every data structure in your application, and you’ll spend more time writing validation code than business logic.

Pydantic takes care of this for you!

---
### Pydantic usage

Pydantic combines three powerful concepts
- type hints
- runtime validation
- automatic serialization

Instead of manual checks, you define your data structure once using Python’s type annotation syntax, and Pydantic handles all the validation automatically!

---
### A basic Pydantic example

```
from pydantic import BaseModel, EmailStr
from typing import Optional

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

user = User(**user_data)
print(user.age)  # 25 (as integer)
print(user.model_dump())  # Clean dictionary output
```

---
### Features

Pydantic gives you several benefits
- Performance => written in Rust, making it fast!
- Integration => modern frameworks like FastAPI use Pydantic models!

---
### Example in FastAPI 

```
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
   name: str
   email: EmailStr
   age: int

@app.post("/users/")
async def create_user(user: UserCreate):
   # FastAPI automatically validates the request body
   # and generates API docs from your Pydantic model
   return {"message": f"Created user {user.name}"}
```

JSON schema generation is automatic with every Pydantic model!

---
### Alternatives

- Dataclasses => Built-in container objects
- Marshmallow => Third Party alternative

---
### Pydantic vs Dataclasses

Decision comes down to validation needs!

- Python’s @dataclass is perfect for simple data containers where you trust the input
- Pydantic excels when you need validation, serialization, and integration with web frameworks

---
### Pydantic vs Dataclasses (2)

```
from dataclasses import dataclass
from pydantic import BaseModel

# Dataclass: fast, simple, no validation
@dataclass
class UserDataclass:
   name: str
   age: int

# Pydantic: validation, serialization, framework integration
class UserPydantic(BaseModel):
   name: str
   age: int

```

---
### Pydantic vs Marshmallow

Pydantic 
 - better performance and integration with modern async frameworks!
 - type hint approach feels more natural to Python developers

Marshmallow uses schema classes:

```
from dataclasses import dataclass, field
import datetime as dt

@dataclass
class User:
    name: str
    email: str
    created_at: dt.datetime = field(default_factory=dt.datetime.now)

from marshmallow import Schema, fields
class UserSchema(Schema):
    name = fields.Str()
    email = fields.Email()
    created_at = fields.DateTime()
```

---
###  How to install Pydantic

execute the command:
```
uv add pydantic
```

or use pip:
```
pip install pydantic
```

---
### Email validation

When you want e-mail validation in you models, you have to add that package as well:
```
uv add "pydantic[email]"
```
or use pip
```
pip install "pydantic[email]"
```

---
### Your first Pydantic model

Let’s build a simple user model to see Pydantic in action. 

```
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class User(BaseModel):
   name: str
   email: EmailStr
   age: int
   is_active: bool = True
   created_at: datetime = None

# Test with clean data
clean_data = {
   "name": "Alice Johnson",
   "email": "alice@example.com",
   "age": 28
}

user = User(**clean_data)
print(f"User created: {user.name}, Age: {user.age}")
print(f"Model output: {user.model_dump()}")
```

Output:
```
User created: Alice Johnson, Age: 28
Model output: {'name': 'Alice Johnson', 'email': 'alice@example.com', 'age': 28, 'is_active': True, 'created_at': None}
```

---
### What did we create?

Explanation:
- Inherit from BaseModel
   - has all of Pydantic's validation and serialization capabilities
- Field definitions
   - each line in the class defines a field with its expected type
   - EmailStr is a special that automatically validates email addresses
- Default values
   - fields like is_active: bool = True have default values
   - The = None for created_at makes this field optional
- Model instantiation User(**clean_data)
    - the ** unpacks dictionary and passes each key-value pair as keyword arguments to model constructor

---
### Automatic type conversion
Now let’s see Pydantic’s automatic type conversion in action:

```
# Messy data that still works
messy_data = {
   "name": "Bob Smith",
   "email": "bob@company.com",
   "age": "35",  # String instead of int
   "is_active": "true"  # String instead of bool
}

user = User(**messy_data)
print(f"Age type: {type(user.age)}")  # <class 'int'>
print(f"Is active type: {type(user.is_active)}")  # <class 'bool'>
```

---
### Validation failure
When validation fails, Pydantic provides clear error messages:

```
from pydantic import ValidationError

try:
   invalid_user = User(
       name="",  # Empty string
       email="not-an-email",  # Invalid email
       age=-5  # Negative age
   )
except ValidationError as e:
   print(e)
```
```
1 validation error for User
email
 value is not a valid email address: An email address must have an @-sign. [type=value_error, input_value='not-an-email', input_type=str]
```

---
### BaseModel vs. dataclasses

- Python dataclasses are perfect for simple data containers where you control the input:

```
from dataclasses import dataclass

@dataclass
class ProductDataclass:
   name: str
   price: float
   in_stock: bool

# Fast, simple, but no validation
product = ProductDataclass("Laptop", 999.99, True)

# This also works, even though types are wrong:
broken_product = ProductDataclass(123, "expensive", "maybe")
```

---
### Pydantic models

Pydantic models add validation, serialization, and framework integration

```
from pydantic import BaseModel, Field

class ProductPydantic(BaseModel):
   name: str = Field(min_length=1)
   price: float = Field(gt=0)  # Must be greater than 0
   in_stock: bool

# Automatic validation prevents bad data
try:
   product = ProductPydantic(name="", price=-10, in_stock="maybe")
except ValidationError as e:
   print("Validation caught the errors!")

# Valid data works perfectly
good_product = ProductPydantic(
   name="Laptop",
   price="999.99",  # String converted to float
   in_stock=True
)
```

---
### Which to choose

- Use dataclasses for 
    - internal data structures
    - configuration objects 
    - when performance is critical and you trust your data sources

- Use Pydantic for 
    - API endpoints
    - user input
    - external data parsing
    - when you need JSON serialization

For web applications, the automatic integration with FastAPI makes Pydantic the clear choice!


---
### Building Data Models With Pydantic

Example scenario:

*Consider a product catalog API where price data comes from multiple vendors with different formatting standards. Some send prices as strings, others as floats, and occasionally, someone sends a negative price that crashes your billing system*


---
### Implementation

This could result into the following model:

```
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional

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
```


---
### Fields explanation
Each Field() parameter serves a specific purpose
 - min_length and max_length prevent database schema violations
 - gt and le create business logic boundaries
 - pattern validates formatted data using regular expressions
 
 The Field(...) syntax with ellipsis marks the required fields, while Field(None, ...) creates optional fields with validation rules

---
### Type coercion vs strict validation
By default, Pydantic converts compatible types 

This flexibility works well for user input, some scenarios need exact type matching:

```
from pydantic import BaseModel, Field, ValidationError

# Default: lenient type coercion
class FlexibleOrder(BaseModel):
   order_id: int
   total_amount: float
   is_paid: bool

# These all work due to automatic conversion
flexible_order = FlexibleOrder(
   order_id="12345",  # String to int
   total_amount="99.99",  # String to float
   is_paid="true"  # String to bool
)

# Strict validation when precision matters
class StrictOrder(BaseModel):
   model_config = {"str_strip_whitespace": True, "validate_assignment": True}
  
   order_id: int = Field(strict=True)
   total_amount: float = Field(strict=True)
   is_paid: bool = Field(strict=True)
```

---
### Nested models and complex data
Real applications handle complex, interconnected data structures. 

*An e-commerce order contains customer information, shipping addresses, and multiple product items ,  each requiring its own validation*

```
from typing import List
from datetime import datetime

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
```

---
### Explanation
Pydantic validates nested structures recursively

- Customer field becomes a full Customer object, which validates its own Address field
- List[OrderItem] syntax validates each list element as an OrderItem, while Field(min_length=1) prevents empty orders from reaching your inventory system. 
- Using default_factory=datetime.now creates unique timestamps for each order instance.

---
### Optional fields and None handling
Different operations need different data requirements.

- user creation demands complete information
- user updates should accept partial changes

```
from typing import Optional

class UserCreate(BaseModel):
   name: str = Field(min_length=1)
   email: EmailStr
   age: int = Field(ge=13, le=120)
   phone: Optional[str] = Field(None, pattern=r'^\+?1?\d{9,15}$')

class UserUpdate(BaseModel):
   name: Optional[str] = Field(None, min_length=1)
   email: Optional[EmailStr] = None
   age: Optional[int] = Field(None, ge=13, le=120)
   phone: Optional[str] = Field(None, pattern=r'^\+?1?\d{9,15}$')

# PATCH request with partial data
update_data = {"name": "Jane Smith", "age": 30}
user_update = UserUpdate(**update_data)

# Serialize only provided fields
patch_data = user_update.model_dump(exclude_none=True)
print(f"Fields to update: {list(patch_data.keys())}")
```

---
### Same code with modern/alternative syntax

```
Python
from typing import Annotated
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    email: EmailStr
    age: Annotated[int, Field(ge=13, le=120)]
    phone: Annotated[str | None, Field(pattern=r'^\+?1?\d{9,15}$')] = None

class UserUpdate(BaseModel):
    name: Annotated[str | None, Field(min_length=1)] = None
    email: EmailStr | None = None
    age: Annotated[int | None, Field(ge=13, le=120)] = None
    phone: Annotated[str | None, Field(pattern=r'^\+?1?\d{9,15}$')] = None

# PATCH request with partial data
update_data = {"name": "Jane Smith", "age": 30}
user_update = UserUpdate(**update_data)

# Serialize only fields explicitly set in input
patch_data = user_update.model_dump(exclude_unset=True)
print(f"Fields to update: {list(patch_data.keys())}")
```

---
### Same code with modern/alternative syntax

Changes
- Annotated Metadata pattern
   - decouples pure Python type annotations from Pydantic runtime rules (Field).
- | None Union Syntax
   - replaces Optional[...] with native Python 3.10+ syntax.
- exclude_unset=True for PATCH
   - replaces exclude_none=True
   - this allows a client to explicitly pass "email": null to clear a field in the database, whereas exclude_none=True would strip the update entirely

---
### exclude_none vs exclude_unset

```
class UserUpdate(BaseModel):
    name: str | None = None
    age: int | None = None

# 'age' is unprovided; 'name' is explicitly set to None
user = UserUpdate(name=None)

user.model_dump(exclude_none=True)  
# Output: {} 
# Strips both fields because both hold a value of None.

user.model_dump(exclude_unset=True) 
# Output: {'name': None} 
# Keeps 'name' because it was provided, but drops 'age' because it was left unset.
```

---
### Serialization and deserialization
Serialization converts Pydantic objects back into dictionaries or JSON strings for storage or transmission. 

The model_dump() method handles this conversion
- exclude_none=True => removes any field whose value evaluates to None
- exclude_unset=True => removes unprovided fields

The model_validate() method handles dictionary to object deseralization
- generates a validated object instance from a dictionary


---
### Custom Validation 

How do you handle data that doesn’t fit standard type-checking patterns?

A scenario:

*Consider a user registration form where password requirements vary based on subscription plans, or an API that receives address data from multiple countries with different postal code formats. These scenarios require custom validation logic that captures your specific business rules while integrating smoothly with web frameworks and configuration systems.*

---
### Field validator decorator
Consider a user registration system where different subscription tiers have different password requirements:

```
from pydantic import BaseModel, field_validator, Field
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
```

---
### Field_validator decorator 

The @field_validator decorator on a @classmethod gives the method validation purpose
- info.data => holds data for the other members, validated

The validator runs after basic type checking passes, so you can safely assume the subscription_tier is one of the allowed value!

---
### Model_validator decorator 
For validation that spans multiple fields, the @model_validator decorator runs after all individual fields are validated:

```
from datetime import datetime
from pydantic import model_validator

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
```

---
### Model validator decorator 

More details:
   - mode='after' parameter ensures the validator receives a fully constructed model instance
   - the validator function must return self to indicate successful validation

---
### FastAPI integration
FastAPI’s integration creates:
   - automatic request validation
   - API documentation

---
### The Key Pattern
The key pattern involves creating separate models for different operations:

```
from fastapi import FastAPI
from typing import Optional
from datetime import datetime

app = FastAPI()

class UserCreate(BaseModel):
   username: str = Field(min_length=3)
   email: EmailStr
   password: str = Field(min_length=8)

class UserResponse(BaseModel):
   id: int
   username: str
   email: EmailStr
   created_at: datetime
  
@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate):
   # FastAPI automatically validates the request body
   new_user = {
       "id": 1,
       "username": user.username,
       "email": user.email,
       "created_at": datetime.now()
   }
   return UserResponse(**new_user)
```

---
### Separation Input/Output

This seperation provides benefits
- Input models can include validation rules and required fields
- Output models control exactly what data gets sent to clients

FastAPI automatically generates OpenAPI documentation from your Pydantic models, creating interactive API docs that developers can use to test endpoints.

---
### How about update models?
For update operations, you can create models where all fields are optional:

```
class UserUpdate(BaseModel):
    username: Annotated[str | None, Field(min_length=3)] = None
    email: EmailStr | None = None

@app.patch("/users/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate):
    # Extract only explicitly sent fields in the payload
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Database update logic using update_data goes here
    
    return {"message": f"Updated user {user_id}", "updated_fields": update_data}
```

The exclude_unset=True parameter in PATCH operations ensures you only update fields that were explicitly provided, preventing accidental overwrites. 

This pattern works perfectly for REST APIs where clients send partial updates.

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Basic Pydantic


---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Pydantic Models


