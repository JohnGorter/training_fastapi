# Demo 6. Pydantic Env

### step 1. create project
Create a new project with uv --no-package and name it demo_pydantic env.

Make sure to add the pydantic and pydantic-settings package to the project. 

### step 2. Replace the code

Open the ./main.py from the project root folder and copy the contents below to this file:

```
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "demo-pydantic-env"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()

print(f"App Name: {settings.app_name}")
print(f"Debug Mode: {settings.debug}")
```

### step 3. Create an .env file
In the project root folder, create an .env file with the following contents:
```
DEBUG=True
```

Save this file and run the code using
```
uv run ./main.py
```

If all went well, the code should output
```
Debug Mode: True
```

### step 4. Override the env file

To override the env file, we can use the following command line to define a value for an environment variable
```
export DEBUG=False
```

in the terminal where this command is executed, rerun the ./main.py with the following code
```
uv run ./main.py
```

After running the code, the output should now be
```
Debug Mode: False
```

This succesfully shows the setting functionality from Pydantic

### Step 5. Nested settings

Open the ./main.py and copy and paste this code into the file

```
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

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

print(f"Debug: {settings.debug}")
print(f"Database URL: {db_url}")
```

Save this file and run the code using
```
uv run ./main.py
```

If all went well, the code should output
```
Debug: False
Database URL: odbc://username:password@localhost:1433/database_name
```

Explain the workings
