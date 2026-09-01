# Pydantic env 

---
### Environment Variables

Production applications need secure, deployment-friendly configuration management. 

Pydantic’s BaseSettings combined with .env files provides type-safe configuration that works across development, staging, and production environments!

---
### Environment Variables

How does this work:

```
# .env file
DATABASE_URL=postgresql://user:password@localhost:5432/myapp
SECRET_KEY=your-secret-key-here
DEBUG=false
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```
```
# your py file
from pydantic import BaseSettings, Field
from typing import List

class AppSettings(BaseSettings):
    database_url: str = Field(description="Database connection URL")
    secret_key: str = Field(description="Secret key for JWT tokens")
    debug: bool = Field(default=False)
    allowed_hosts: List[str] = Field(default=["localhost"])
  
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

# Load settings automatically from environment and .env file
settings = AppSettings()
```

---
### BaseSettings
The BaseSettings class 
    - automatically reads from environment variables
    - .env files, 
    - command-line arguments 
    
Environment variables take precedence over .env file values, making it easy to override settings in different deployment environments!

The case_sensitive = False setting allows flexible environment variable naming!

---
### BaseSettings(2)

For complex applications, you can organize settings into logical groups:

```
class DatabaseSettings(BaseSettings):
    url: str = Field(validation_alias="DATABASE_URL")
    max_connections: int = Field(default=5, validation_alias="DB_MAX_CONNECTIONS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

class AppSettings(BaseSettings):
    debug: bool = False
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = AppSettings()
# Access nested configuration
db_url = settings.database.url
```

---
### BaseSettings (3)

Summary:

*The .env file approach works with deployment platforms like Heroku, AWS, and Docker, where environment variables are the standard way to configure applications. Your application gets type safety and validation while following cloud-native configuration patterns that operations teams expect.*

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Environment Pydantic

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
There is no Lab for this chapter!


