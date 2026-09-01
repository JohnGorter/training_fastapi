
step 1: create a new uv project, name it demo_pydantic_env (use --no-package)
step 2: install pydantic using: uv add pydantic
step 3: install pydantic-settings using: uv add pydantic-settings
step 4. create an .env file and give it the following code:
```
DEBUG=True

# export DEBUG=False
```
step 2: add the following code to the main.py file:
    ```
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "demo-pydantic-env"

    debug: bool = False
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def main():
    print("Hello from demo-pydantic-env!")
    settings = Settings()

    print(f"App Name: {settings.app_name}")
    print(f"Debug Mode: {settings.debug}")

if __name__ == "__main__":
    main()
    ```

step 5: run this code using uv run ./main.py and check to see debugging mode is set
step 6: on the command line, export a new environment variable and show that this
takes precedence over the .env file
```
export Debug=False
```

