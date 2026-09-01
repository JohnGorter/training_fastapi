# Demo 2. RequestParameters

### Step 1. Execute requests
Open the project demo_requestparameters and execute the following commands and explain the workings:
```
# basic request with the default parameters
http localhost:8000/products/search

# query string parameters, notice the quotes are required
http "localhost:8000/products/search?q=john"

# use command line arguments as query string parameter (notice the ==)
http localhost:8000/products/search q==john

# multiple query string parameters
http localhost:8000/products/search q==john max_price==10

# show only the body, not the headers
http -b "localhost:8000/products/search?q=john"

# show the request and the response
http -v "localhost:8000/products/search?q=john"

# show that query string parameters that are not know in the function are ignored
http -v "localhost:8000/products/search?category=john"

# show that incorrect types generate an error
http -v "localhost:8000/products/search?max_price=john"
```

### Step 2. More Requests
Use the following commands to test the body parameters
```
# show that a default post results in an error of missing values
http POST localhost:8000/checkout/pay

# notice the = assignment instead of == to set a json body and := for items for non string values
http POST localhost:8000/checkout/pay idempotency_key=1 items:='[{"sku":"1","price":10}]'

# alternative syntax for json
http POST localhost:8000/checkout/pay idempotency_key=1 "items[0][sku]=1" "items[0][price]:=10"

```

### Step 3. Even more requests
Use the following commands to test the header parameters
```
# notice the : name value and the - instead of the _ that is used in the code
# - is translated into _ in python, - is not a valid character so header is x-api-key
http -v localhost:8000/analytics/metrics x-api-key:1234

```

### Step 4. And more requests
Use the following command to test the cookie parameters
```
# notice now we DO use the _ because it is a vairable name, not a header and we 
# also use a single =
http localhost:8000/user/profile Cookie:session_id=foo
```

### Step 5. Final request
Use the following command to test form parameters
```
# notice the --form which has to be the first argument
http --form POST localhost:8000/auth/login username=john password=test  

# or use the shorter
http -f POST localhost:8000/auth/login username=john password=test  
```

### Step 6. Actually one lasts request
Use the following command to test file upload parameters
```
http -f POST localhost:8000/documents/ocr document@main.py
```