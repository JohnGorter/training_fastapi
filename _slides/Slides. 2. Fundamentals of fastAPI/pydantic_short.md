# Pydantic

---
### What is Pydantic
Pydantic is the most widely used data validation library for Python

---
### How to install


using uv: 
```
uv add pydantic
```

For fastapi it is already installed

using pip
```
pip install pydantic
```

---
### How does it work

To make it work, you create a class based on ModelBase and use type hints to 
annotate members. 
- these hints are used for the validation of data

Pydantic can map data from and to JSON for serialization, so that is very helpfull.


---
### An example

Given this definition of a User: 
```
from datetime import datetime
from pydantic import BaseModel, PositiveInt

class User(BaseModel):
  id: int  
  name: str = 'John Doe'  
  signup_ts: datetime | None  
  tastes: dict[str, PositiveInt]  
```


---
### An example (2)

We can feed it JSON data for population:
```
external_data = {
  'id': 123,
  'signup_ts': '2019-06-01 12:22',  
  'tastes': {
      'wine': 9,
      'cheese': 7,  
      'cabbage': '1',  
  },
}
user = User(**external_data)  
print(user.id)  
```

---
### An example (2)

It raises an error when the data does not validate:
```
external_data = {'id': 'not an int', 'tastes': {}}  
try:
  User(**external_data)  
except ValidationError as e:
  print(e.errors())
```

shows:
```
[
      {
          'type': 'int_parsing',
          'loc': ('id',),
          'msg': 'Input should be a valid integer, unable to parse string as an integer',
          'input': 'not an int',
          'url': 'https://errors.pydantic.dev/2/v/int_parsing',
      },
      {
          'type': 'missing',
          'loc': ('signup_ts',),
          'msg': 'Field required',
          'input': {'id': 'not an int', 'tastes': {}},
          'url': 'https://errors.pydantic.dev/2/v/missing',
      },
  ]
```

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Basic Pydantic


---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Pydantic

