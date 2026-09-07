# Jinja2 Templates

---
### Jinja2 Templates

Jinja2Templates initializes the template rendering engine targeting a specific directory

TemplateResponse compiles HTML files with injected Python context data

Real-World Use Case
- rendering dynamic web pages, email bodies, or user account dashboards

Behavior
- FastAPI requires passing the current request object to TemplateResponse

---
### Jinja2 Templates

```
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/welcome")
async def welcome_page(request: Request, username: str = "Guest"):
    return templates.TemplateResponse(
        request=request,
        name="welcome.html",
        context={"username": username, "status": "Active"}
    )
```

---
### Static Asset Referencing 

Jinja2 templates use url_for() to generate dynamic URL paths for mounted static files and endpoints, preventing hardcoded broken links when application routes change

Real-World Use Case
- referencing global stylesheet bundles 

Behavior
- url_for('static', path='css/styles.css') resolves to /static/css/styles.css automatically

---
### Static Asset Referencing 

```
# templates/base.html (Jinja2 Layout)HTML:
<!DOCTYPE html>
<html>
<head>
    <!-- Dynamic static asset path resolving -->
    <link rel="stylesheet" href="{{ url_for('static', path='css/styles.css') }}">
</head>
<body>
   ...
</body>
</html>
```

---
### Template inheritance

Template inheritance in Jinja2 applies the Don't Repeat Yourself (DRY) principle to UI design

You build a single base "skeleton" template containing global HTML wrappers, navbars, and assets, while child templates inherit that structure and fill in or override specific content blocks

---
### Base Layout Skeletons ({% block %})

The parent template defines the structural HTML shell (<html>, <head>, <body>) and marks dynamic placeholders using {% block block_name %} tags

Real-World Use Case
- maintaining a single source of truth for global site navigation, footer copyright notices, and primary CSS framework links

Behavior
- text or elements placed inside a base block act as fallback default content if a child template chooses not to override it

---
### Base Layout Skeletons ({% block %})

```
# HTML<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}Enterprise Portal{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', path='css/app.css') }}">
    {% block extra_styles %}{% endblock %}
</head>
<body>
    <header><nav>Global Navigation</nav></header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

---
### Child Layout Extension ({% extends %})

Child templates declare their parent using {% extends "parent.html" %} and target specific block names to inject custom HTML content

real-World Use Case
- building unique view pages (e.g., User Profile, Settings, Reports) that share the exact same UI wrapper

Behavior
- {% extends %} must be the very first tag in the child template
- any HTML written outside of a {% block %} in a child template is ignored 

---
### Child Layout Extension ({% extends %})

```
# HTML<!-- templates/profile.html -->
{% extends "base.html" %}

{% block title %}User Profile - Enterprise Portal{% endblock %}

{% block content %}
    <h2>User Profile</h2>
    <p>Welcome back, {{ user.name }}!</p>
{% endblock %}
```

---
### Preserving Parent Content ({{ super() }})

When a child template overrides a block, it completely replaces the parent block's content by default 

- calling {{ super() }} inside a child block pulls in the parent's default markup alongside the child's additions

Real-World Use Case
- appending page-specific JavaScript libraries or CSS stylesheets (like Chart.js for a reporting page) without wiping out global CSS links defined in the parent <head>

Behavior
- injects the parent block’s rendered text directly at the call site

---
### Preserving Parent Content ({{ super() }})

```
# HTML<!-- templates/analytics.html -->
{% extends "base.html" %}

{% block extra_styles %}
    <!-- Keeps any styles in base.html AND appends the chart stylesheet -->
    {{ super() }}
    <link rel="stylesheet" href="{{ url_for('static', path='css/charts.css') }}">
{% endblock %}
```

---
### Multi-Tiered (Nested) Inheritance

Inheritance chains can stretch across multiple layers:
- (Base <- Section Base <- Specific Page)

Real-World Use Case
- an admin portal where all admin pages share a sidebar layout (admin_base.html), which itself inherits from the global site shell (base.html)

Behavior
- blocks cascade down the inheritance tree. Lowest-level children override blocks defined in intermediate or root parents

---
### Multi-Tiered (Nested) Inheritance

```
# HTML<!-- templates/admin/admin_base.html -->
{% extends "base.html" %}

{% block content %}
    <div class="admin-wrapper">
        <aside class="sidebar">Admin Sidebar Navigation</aside>
        <section class="admin-body">
            {% block admin_content %}{% endblock %}
        </section>
    </div>
{% endblock %}
```

---
### Custom Template Filters 

Custom Python functions can be registered directly into Jinja2's filtering pipeline to transform data formatting directly inside HTML templates

Real-World Use Case
- formatting raw floating-point currencies (1250.5 <-  $1,250.50)
- localizing timestamps
- truncating text snippets

Behavior
- filters are executed during template compilation before the final response stream is generated

---
### Custom Template Filters 

```
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Register custom Python filter
def format_currency(value: float) -> str:
    return f"${value:,.2f}"

templates.env.filters["currency"] = format_currency

# Usage inside Jinja HTML template:
# <p>Total: {{ total_price | currency }}</p>
```

---
### Form Processing 

FastAPI combines Form() parameter decoding with Jinja2 rendering to process traditional HTML form submissions without relying on client-side SPA frameworks

Real-World Use Case
- classic server-rendered login screens
- search filter forms
- feedback submissions

Behavior
- extracts application/x-www-form-urlencoded payloads 
- immediately re-renders HTML templates with updated state or validation errors

---
### Form Processing 

```
from typing import Annotated
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.post("/search")
async def handle_search(
    request: Request,
    query: Annotated[str, Form()],
):
    results = ["Laptop", "Monitor"] if query else []
    return templates.TemplateResponse(
        request=request,
        name="search_results.html",
        context={"query": query, "results": results}
    )
```

---
### Unified Enterprise SSR & Static Files Implementation

This production pattern demonstrates static file mounting, Jinja template layout inheritance, custom value formatting filters, form payload processing, and flash messaging in an enterprise order management application

File Structure Setup:
```
Plaintextproject/

├── static/
│   └── css/
│       └── main.css
├── templates/
│   ├── base.html
│   └── order_summary.html
└── main.py
```

main.py (FastAPI Server Application)
```
from datetime import datetime, timezone
from typing import Annotated
from fastapi import FastAPI, Request, Form, Path, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

app = FastAPI()

# 1. Mount Static Asset Subsystem
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Configure Jinja2 Engine
templates = Jinja2Templates(directory="templates")

# 3. Register Custom Template Filters
def format_usd(value: float) -> str:
    return f"${value:,.2f}"

def format_date(value: datetime) -> str:
    return value.strftime("%b %d, %Y %H:%M UTC")

templates.env.filters["usd"] = format_usd
templates.env.filters["datetime"] = format_date

# Simulated Database
ORDERS_DB = {
    101: {"item": "Developer Workstation", "price": 2499.99, "status": "Shipped"}
}

# 4. GET Endpoint: Render Form & Existing Data
@app.get("/orders/{order_id}")
async def show_order_summary(
    request: Request,
    order_id: Annotated[int, Path(ge=100)],
):
    order = ORDERS_DB.get(order_id)
    return templates.TemplateResponse(
        request=request,
        name="order_summary.html",
        context={
            "order_id": order_id,
            "order": order,
            "current_time": datetime.now(timezone.utc)
        }
    )

# 5. POST Endpoint: Handle Form Update & Re-render
@app.post("/orders/{order_id}/update")
async def update_order_status(
    request: Request,
    order_id: Annotated[int, Path(ge=100)],
    new_status: Annotated[str, Form()],
):
    if order_id in ORDERS_DB:
        ORDERS_DB[order_id]["status"] = new_status

    return templates.TemplateResponse(
        request=request,
        name="order_summary.html",
        context={
            "order_id": order_id,
            "order": ORDERS_DB.get(order_id),
            "current_time": datetime.now(timezone.utc),
            "flash_message": f"Order status successfully updated to '{new_status}'."
        }
    )
```

templates/base.html (Master Template Wrapper)
```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}Enterprise Portal{% endblock %}</title>
    <!-- Resolve Static Asset URL via url_for -->
    <link rel="stylesheet" href="{{ url_for('static', path='css/main.css') }}">
</head>
<body>
    <nav><strong>Enterprise Commerce Platform</strong></nav>
    <hr>
    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>
templates/order_summary.html (Child Page Inheritance)HTML{% extends "base.html" %}

{% block title %}Order #{{ order_id }}{% endblock %}

{% block content %}
    <h2>Order Details (#{{ order_id }})</h2>

    {% if flash_message %}
        <div style="color: green;">{{ flash_message }}</div>
    {% endif %}

    {% if order %}
        <p><strong>Item:</strong> {{ order.item }}</p>
        <!-- Apply Registered Custom Filters -->
        <p><strong>Price:</strong> {{ order.price | usd }}</p>
        <p><strong>Status:</strong> {{ order.status }}</p>
        <p><strong>Rendered At:</strong> {{ current_time | datetime }}</p>

        <h3>Update Order Status</h3>
        <form action="/orders/{{ order_id }}/update" method="post">
            <select name="new_status">
                <option value="Processing">Processing</option>
                <option value="Shipped">Shipped</option>
                <option value="Delivered">Delivered</option>
            </select>
            <button type="submit">Update</button>
        </form>
    {% else %}
        <p style="color: red;">Order not found.</p>
    {% endif %}
{% endblock %}
```

---
### Execution Pipeline Explanation

- Asset Delivery (app.mount)
- Request Object Requirement: When calling show_order_summary, FastAPI passes request to TemplateResponse 
- Template Inheritance ({% extends %})
- Filter Execution
- SSR Form Workflow

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Jinja2 templates

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Jinja2 Templates







