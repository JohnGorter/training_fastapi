# FastAPI Cloud 

---
### FastAPI Cloud

FastAPI Cloud is the platform built by the FastAPI team to enable instant, zero-configuration cloud deployments with autoscaling, built-in TLS, and managed secrets directly from the command line

---
###  Basic Project Packaging & Single-Command Deployment 

FastAPI Cloud packages your codebase, auto-detects dependencies, and builds an isolated cloud execution environment without requiring manual Dockerfiles or server provisioning

Real-World Use Case
- pushing a local development API to a live production SSL endpoint

Behavior
- running fastapi deploy parses pyproject.toml to identify application entrypoints 
- uploads matching source files (respecting .gitignore)
- installs dependencies
- provisions the cloud instance

Ini, TOML# pyproject.toml
```
[project]
name = "my-fastapi-app"
version = "0.1.0"
dependencies = [
    "fastapi[standard]>=0.115.0",
    "pydantic-settings>=2.0.0",
]

[tool.fastapi]
entrypoint = "app.main:app"
```
Bash# Command Line Deployment
```
fastapi login
fastapi deploy
```

---
### Managing Secrets & Environment Variables 

Sensitive credentials (database URLs, JWT keys, third-party API tokens) are managed outside source control using fastapi cloud env CLI commands or the web dashboard

Real-World Use Case
- safely injecting encrypted PostgreSQL connection strings and secret keys into cloud app runtimes

Behavior
- passing the --secret flag encrypts variables at rest
- Pydantic's BaseSettings automatically binds incoming environment variables to typed Python configuration fields

Bash# Set standard environment variable
```
fastapi cloud env set ENVIRONMENT "production"
```

```
# Set encrypted secret variable
fastapi cloud env set --secret DATABASE_URL "postgresql+asyncpg://user:pass@db.host:5432/production"
```

Python# app/config.py
```
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    environment: str = "development"
    database_url: str

settings = Settings()
```

---
### Build Optimization & Package Exclusion 

To prevent large, non-essential local files from slowing down build uploads create a 
- .fastapicloudignore file 
in the project root

Real-World Use Case
- excluding local test suites, dataset caches, virtual environments (.venv), and node artifacts from deployment archives

Behavior
- the deployment CLI skips files matching .fastapicloudignore patterns during cloud packaging, reducing archive sizes and accelerating build times

Plaintext# .fastapicloudignore
```
.venv/
tests/
__pycache__/
*.pyc
*.sqlite3
.git/
```

---
### Continuous Integration & Automated CI/CD Pipelines

Automated deployment pipelines (such as GitHub Actions) can deploy updates to FastAPI Cloud non-interactively by supplying an application ID and API token

Real-World Use Case
- auto-deploying main branch commits on GitHub to production upon passing unit test suites

Behavior
- running fastapi deploy --no-wait executes headless packaging without requiring interactive browser authentication prompts

YAML# .github/workflows/deploy.yml
```
name: Deploy to FastAPI Cloud

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3

      - name: Deploy to FastAPI Cloud
        env:
          FASTAPI_CLOUD_APP_ID: ${{ secrets.FASTAPI_CLOUD_APP_ID }}
          FASTAPI_CLOUD_TOKEN: ${{ secrets.FASTAPI_CLOUD_TOKEN }}
        run: |
          uv run fastapi deploy --no-wait
```

---
### Unified Enterprise FastAPI Cloud Deployment Pipeline

This production pattern demonstrates a complete FastAPI application configured for FastAPI Cloud deployment. It integrates Pydantic BaseSettings environment parsing, SQLAlchemy 2.0 Async database connection pooling, Readiness probes, and zero-downtime deployment workflows

app/config.py
```
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "Enterprise Cloud Core"
    environment: str = "production"
    database_url: str = "sqlite+aiosqlite:///cloud_app.db"
    api_secret: str = "default-development-secret"

settings = Settings()
```

app/main.py
```
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from fastapi import FastAPI, Depends, Response, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.config import settings

# ---------------------------------------------------------------------
# 1. DATABASE & LIFESPAN CONFIGURATION
# ---------------------------------------------------------------------
engine = create_async_engine(settings.database_url, echo=False)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure connection infrastructure is ready
    yield
    # Shutdown: Dispose database connections during container recycle
    await engine.dispose()

app = FastAPI(title=settings.app_name, lifespan=lifespan)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# ---------------------------------------------------------------------
# 2. PROBES & PRODUCTION ROUTE HANDLERS
# ---------------------------------------------------------------------
@app.get("/healthz/ready", tags=["Infrastructure"])
async def readiness_probe(response: Response, db: Annotated[AsyncSession, Depends(get_db)]):
    """Readiness check queried by cloud load balancers before routing traffic."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "READY", "environment": settings.environment}
    except Exception as exc:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "UNHEALTHY", "detail": str(exc)}

@app.get("/api/v1/info", tags=["Core API"])
async def get_app_info():
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "cloud_status": "ONLINE"
    }
```

pyproject.toml
```
Ini, TOML[project]
name = "enterprise-cloud-api"
version = "1.0.0"
dependencies = [
    "fastapi[standard]>=0.115.0",
    "pydantic-settings>=2.0.0",
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.20.0",
]

[tool.fastapi]
entrypoint = "app.main:app"
```

Deployment Setup Steps:

Bash# 1. Set runtime environment configuration and secrets
```
fastapi cloud env set ENVIRONMENT "production"
fastapi cloud env set --secret DATABASE_URL "sqlite+aiosqlite:///cloud_app.db"
fastapi cloud env set --secret API_SECRET "prod-super-secret-key-99"
```

Bash# 2. Execute cloud deployment
```
fastapi deploy
```


---
### Execution Pipeline Explanation

- Configuration Resolution: Running fastapi deploy reads pyproject.toml, packages project source code (excluding items in .fastapicloudignore), and uploads the codebase to FastAPI Cloud.  
- Environment & Secret Binding: FastAPI Cloud injects configured secrets (DATABASE_URL, API_SECRET) into the execution runtime. 
- Pydantic Settings binds these values automatically when settings = Settings() initializes.  
- Lifespan Pool Startup: As the container boots, FastAPI runs lifespan, establishing the database connection pool using the injected configuration variables.
- Traffic Routing & Zero-Downtime: The platform queries /healthz/ready. Once the check returns HTTP 200 READY, FastAPI Cloud transitions live traffic to the new app version with zero downtime.