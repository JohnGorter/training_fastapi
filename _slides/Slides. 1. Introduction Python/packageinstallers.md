# Package installers

Install external packages to use in your project

---
### Which package installers are widely used

- Pip => The default, built-in package installer that comes with Python
  - Pros: Omnipresent, simple, beginner-friendly, and connects directly to the Python Package Index (PyPI)
  - Cons: Slow dependency resolution for large projects; does not manage virtual environments or lockfiles automatically
  
---
### Which package installers are widely used (2)

- uv => A blazing-fast, Rust-powered package and project manager
  - Pros: 10 to 100 times faster than pip; replaces pip, virtualenv, pyenv, pipx, and Poetry; handles Python version management and universal lockfiles (uv.lock)
  - Cons: Relatively new ecosystem, though highly compatible with standard workflows


---
### Which package installers are widely used (3)

- Poetry => A popular, reliable dependency and project management tool built for professional Python applications
  - Pros: Clean dependency tracking using pyproject.toml and poetry.lock; excellent support for building and publishing libraries to PyPI
  - Cons: Narrower scope (does not manage multiple Python versions natively) and slower than uv.

---
### Which package installers are widely used (4)

- Conda => A heavy-duty environment and package manager tailored for data science and machine learning
  - Pros: Manages non-Python dependencies (like C libraries, Fortran, or R modules) and system-level tools alongside Python
  - Cons: Slower installation speeds, larger disk space consumption, and packages often pull from conda-forge rather than PyPI

---
### Installation

What about uv:
- UV is a Rust-powered Python package manager that is 10–100x faster than pip
- Install with curl -LsSf https://astral.sh/uv/install.sh | sh
- Initialize projects with uv init and add dependencies with uv add package
- Run scripts with uv run script.py—no manual virtual environment activation needed

UV replaces pip, virtualenv, pyenv, and pip-tools in a single tool

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Installing uv and creating your first application

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
PackageInstallers
