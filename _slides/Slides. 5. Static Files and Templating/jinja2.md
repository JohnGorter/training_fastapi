# Jinja2 Templates

---
### Jinja2 Templates

Jinja2Templates initializes the template rendering engine targeting a specific directory

TemplateResponse compiles HTML files with injected Python context data

Real-World Use Case
- rendering dynamic web pages, email bodies, or user account dashboards

Behavior
- FastAPI requires passing the current request object to TemplateResponse

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
#### Form Processing 

FastAPI combines Form() parameter decoding with Jinja2 rendering to process traditional HTML form submissions without relying on client-side SPA frameworks

Real-World Use Case
- classic server-rendered login screens
- search filter forms
- feedback submissions

Behavior
- extracts application/x-www-form-urlencoded payloads 
- immediately re-renders HTML templates with updated state or validation errors

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

<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Jinja2 templates

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Jinja2 Templates













FastAPI handles Server-Side Rendering (SSR) and static asset management by integrating Starlette’s StaticFiles middleware and Jinja2Templates engine over the ASGI protocol. Static assets (CSS, JavaScript, media) are served directly from disk with automatic HTTP caching, while Jinja2 interpolates Python objects into dynamic HTML layouts using streaming ASGI responses.1. Mounting Static Files (StaticFiles & app.mount)Mounting binds an isolated directory on disk to an HTTP route prefix (e.g., /static). This bypasses standard FastAPI route execution entirely, handing control to Starlette's high-performance file-streaming engine.Real-World Use Case: Delivering site-wide CSS stylesheets, JavaScript bundles, company logos, and public downloads.Behavior: Handled directly at the ASGI transport layer. Automatically handles HTTP byte ranges, ETag generation, 304 Not Modified conditional headers, and disk-level caching.Pythonfrom fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mounts the local disk directory 'static' to the URL path '/static'
app.mount("/static", StaticFiles(directory="static"), name="static")
2. Template Engine Initialization (Jinja2Templates) & Basic RenderingJinja2Templates initializes the template rendering engine targeting a dedicated views directory. TemplateResponse compiles HTML files with injected Python context data before writing to the response socket.Real-World Use Case: Rendering dynamic server-side pages like hardware dashboard cards or user profile summaries.Behavior: FastAPI requires passing the current Request object into TemplateResponse so Starlette can resolve context metadata, cookies, headers, and internal URL generation.Pythonfrom fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/hardware/{asset_id}")
async def get_asset_page(request: Request, asset_id: str):
    # Simulated DB record
    asset_data = {"name": "Rack Server X100", "status": "Operational", "cost": 4500.0}
    
    return templates.TemplateResponse(
        request=request,
        name="asset_detail.html",
        context={"asset_id": asset_id, "asset": asset_data}
    )
3. Dynamic Layout Inheritance & Asset Linking (url_for)Jinja2 templates use {% extends %} and {% block %} to maintain modular UI components (navbars, footers). The url_for() template function dynamically resolves paths for static assets and API routes, eliminating brittle, hardcoded file paths.Real-World Use Case: Constructing a consistent site-wide design framework across dozens of internal admin screens.Behavior: url_for('static', path='css/app.css') inspects mounted applications and evaluates the exact path (e.g., /static/css/app.css), even if the application is hosted behind a reverse proxy sub-path.templates/base.html (Master Wrapper Layout)HTML<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}Asset Management System{% endblock %}</title>
    <!-- Dynamic asset path generation -->
    <link rel="stylesheet" href="{{ url_for('static', path='css/app.css') }}">
</head>
<body>
    <nav><strong>Enterprise IT Portal</strong></nav>
    <hr>
    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>
4. Registering Custom Jinja Filters & Global VariablesCustom Python functions can be registered directly into templates.env.filters to transform raw backend data inside HTML layouts. Application-wide constants can be added to templates.env.globals.Real-World Use Case: Formatting raw floating-point currencies (4500.0 $\rightarrow$ $4,500.00), converting UTC timestamps into localized strings, or exposing global organization branding metadata.Behavior: Filters process context variables synchronously during template compilation before the final HTML string stream is generated.Pythonfrom datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 1. Register Custom Filter Functions
def format_usd(amount: float) -> str:
    return f"${amount:,.2f}"

def format_utc_date(dt: datetime) -> str:
    return dt.strftime("%B %d, %Y - %H:%M UTC")

templates.env.filters["usd"] = format_usd
templates.env.filters["utc_date"] = format_utc_date

# 2. Register Global Variables accessible in ALL templates
templates.env.globals["COMPANY_NAME"] = "Nexus Cloud Corp"
templates.env.globals["CURRENT_YEAR"] = 2026

# Usage inside HTML templates:
# {{ asset.cost | usd }} -> $4,500.00
# {{ asset.updated_at | utc_date }} -> August 24, 2026 - 16:00 UTC
# <footer>&copy; {{ CURRENT_YEAR }} {{ COMPANY_NAME }}</footer>
5. Processing HTML Forms, Validation, & Flash Alert MessagingFastAPI captures traditional HTML <form> POST submissions using Form() parameters. When form data passes or fails validation, route handlers re-render Jinja templates with updated state, validation error lists, or flash alerts.Real-World Use Case: Processing server-rendered hardware status changes or maintenance log entries without requiring a single-page application (SPA) JavaScript framework.Behavior: Decodes application/x-www-form-urlencoded payloads directly into typed Python variables or Pydantic models.Pythonfrom typing import Annotated
from fastapi import FastAPI, Request, Form, status
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.post("/hardware/{asset_id}/decommission")
async def decommission_asset(
    request: Request,
    asset_id: str,
    reason: Annotated[str, Form(min_length=10, description="Mandatory audit log reason")],
    approved_by: Annotated[str, Form()],
):
    # Process business logic...
    return templates.TemplateResponse(
        request=request,
        name="asset_detail.html",
        context={
            "asset_id": asset_id,
            "asset": {"name": "Rack Server X100", "status": "Decommissioned", "cost": 4500.0},
            "flash_alert": f"Asset {asset_id} successfully decommissioned by {approved_by}.",
            "alert_type": "success"
        }
    )
Unified Enterprise SSR & Static Asset PipelineThis production pattern combines static file mounting, Jinja layout inheritance, custom value formatting filters, dynamic application globals, HTML form handling, and flash status messaging into a complete hardware inventory management portal.Directory Structure:Plaintextproject/
├── static/
│   └── css/
│       └── app.css
├── templates/
│   ├── base.html
│   └── asset_portal.html
└── main.py
static/css/app.cssCSSbody { font-family: system-ui, sans-serif; margin: 2rem; background-color: #f8f9fa; }
.card { background: #fff; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.alert-success { background: #d4edda; color: #155724; padding: 0.75rem; border-radius: 4px; margin-bottom: 1rem; }
.alert-danger { background: #f8d7da; color: #721c24; padding: 0.75rem; border-radius: 4px; margin-bottom: 1rem; }
.badge { background: #007bff; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.85rem; }
main.py (FastAPI Application Server)Pythonfrom datetime import datetime, timezone
from typing import Annotated
from fastapi import FastAPI, Request, Form, Path, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

app = FastAPI(title="IT Asset Portal")

# 1. Mount Static Files Middleware
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Configure Jinja2 Engine
templates = Jinja2Templates(directory="templates")

# 3. Custom Filters
def format_usd(amount: float) -> str:
    return f"${amount:,.2f}"

def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%b %d, %Y - %H:%M:%S UTC")

templates.env.filters["usd"] = format_usd
templates.env.filters["datetime"] = format_timestamp

# 4. Global Template Constants
templates.env.globals["SYSTEM_NAME"] = "Nexus Enterprise Asset Manager"
templates.env.globals["CURRENT_YEAR"] = 2026

# Simulated Hardware Database
ASSET_DATABASE = {
    "SRV-9021": {
        "name": "Database Host Node 01",
        "category": "Compute",
        "purchase_cost": 12850.50,
        "status": "Active",
        "last_inspected": datetime(2026, 8, 20, 14, 30, tzinfo=timezone.utc),
    }
}

# 5. GET Endpoint: Display Asset Record
@app.get("/portal/assets/{asset_id}")
async def view_asset(
    request: Request,
    asset_id: Annotated[str, Path(description="Hardware Tag Identifier")],
):
    asset = ASSET_DATABASE.get(asset_id)
    return templates.TemplateResponse(
        request=request,
        name="asset_portal.html",
        context={
            "asset_id": asset_id,
            "asset": asset,
            "flash_alert": None if asset else f"Asset ID '{asset_id}' not found.",
            "alert_type": "danger" if not asset else "info",
        }
    )

# 6. POST Endpoint: Handle Maintenance State Updates
@app.post("/portal/assets/{asset_id}/update")
async def update_asset_status(
    request: Request,
    asset_id: Annotated[str, Path()],
    new_status: Annotated[str, Form()],
    inspector_notes: Annotated[str, Form(min_length=5)],
):
    asset = ASSET_DATABASE.get(asset_id)
    if not asset:
        return templates.TemplateResponse(
            request=request,
            name="asset_portal.html",
            context={"asset_id": asset_id, "asset": None, "flash_alert": "Update failed. Record missing.", "alert_type": "danger"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Mutate DB state
    asset["status"] = new_status
    asset["last_inspected"] = datetime.now(timezone.utc)

    return templates.TemplateResponse(
        request=request,
        name="asset_portal.html",
        context={
            "asset_id": asset_id,
            "asset": asset,
            "flash_alert": f"Asset status updated to '{new_status}'. Log entry saved.",
            "alert_type": "success",
        }
    )
templates/base.html (Master Template Shell)HTML<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}{{ SYSTEM_NAME }}{% endblock %}</title>
    <!-- Dynamic resolution of static CSS asset location -->
    <link rel="stylesheet" href="{{ url_for('static', path='css/app.css') }}">
</head>
<body>
    <header>
        <h2>{{ SYSTEM_NAME }}</h2>
    </header>
    <hr>
    
    <main>
        {% block content %}{% endblock %}
    </main>

    <footer style="margin-top: 3rem; font-size: 0.8rem; color: #6c757d;">
        &copy; {{ CURRENT_YEAR }} Infrastructure Operations Core. All rights reserved.
    </footer>
</body>
</html>
templates/asset_portal.html (Child View Layout)HTML{% extends "base.html" %}

{% block title %}Asset #{{ asset_id }} - {{ SYSTEM_NAME }}{% endblock %}

{% block content %}
    <!-- Flash Banner Rendering -->
    {% if flash_alert %}
        <div class="alert-{{ alert_type }}">
            {{ flash_alert }}
        </div>
    {% endif %}

    {% if asset %}
        <div class="card">
            <h3>{{ asset.name }} <span class="badge">{{ asset.status }}</span></h3>
            <p><strong>Hardware Tag:</strong> <code>{{ asset_id }}</code></p>
            <p><strong>Category:</strong> {{ asset.category }}</p>
            <!-- Custom Filter Transformations -->
            <p><strong>Valuation:</strong> {{ asset.purchase_cost | usd }}</p>
            <p><strong>Last Inspection:</strong> {{ asset.last_inspected | datetime }}</p>

            <hr>

            <h4>Log Maintenance Inspection</h4>
            <form action="/portal/assets/{{ asset_id }}/update" method="post">
                <p>
                    <label>New Operational Status:</label><br>
                    <select name="new_status">
                        <option value="Active" {% if asset.status == 'Active' %}selected{% endif %}>Active</option>
                        <option value="Under Maintenance">Under Maintenance</option>
                        <option value="Decommissioned">Decommissioned</option>
                    </select>
                </p>
                <p>
                    <label>Inspector Notes:</label><br>
                    <textarea name="inspector_notes" rows="3" style="width: 100%;" required></textarea>
                </p>
                <button type="submit">Submit Audit Log</button>
            </form>
        </div>
    {% else %}
        <p><a href="/portal/assets/SRV-9021">Return to Default Asset (SRV-9021)</a></p>
    {% endif %}
{% endblock %}
Execution Pipeline Explanation:Static Asset Handshake: When the client loads the rendered HTML page, the browser requests /static/css/app.css. app.mount("/static", ...) handles the file fetch directly from disk, streaming the response with HTTP 200 OK (or 304 Not Modified).Request & Context Lifecycle: view_asset receives an HTTP request for /portal/assets/SRV-9021. The endpoint looks up SRV-9021 in ASSET_DATABASE and calls templates.TemplateResponse(), supplying request alongside custom context variables.Template Compilation Pipeline:Extends Lookup: Jinja loads asset_portal.html, detects {% extends "base.html" %}, and loads base.html as the layout frame.Global Ingestion: Identifies {{ SYSTEM_NAME }} and {{ CURRENT_YEAR }}, pulling values directly from templates.env.globals.Filter Pipeline Execution: Identifies asset.purchase_cost | usd and asset.last_inspected | datetime, executing format_usd(12850.50) and format_timestamp(...) to yield $12,850.50 and Aug 20, 2026 - 14:30:00 UTC.Dynamic Asset Binding: Evaluates {{ url_for('static', path='css/app.css') }} via Starlette's internal router, generating /static/css/app.css.Form Submission & SSR Re-render: Submitting the inspection form sends a POST request (application/x-www-form-urlencoded) to /portal/assets/SRV-9021/update. FastAPI parses new_status and inspector_notes via Form(), updates ASSET_DATABASE, and re-renders asset_portal.html with an updated last_inspected timestamp and a green success alert banner.