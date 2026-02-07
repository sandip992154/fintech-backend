# Development Tools Configuration

## 🛠️ Recommended Development Setup

### VS Code Extensions
Create `.vscode/extensions.json`:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "charliermarsh.ruff",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "ms-python.pylint",
    "ms-toolsai.jupyter",
    "tamasfe.even-better-toml",
    "bradlc.vscode-tailwindcss"
  ]
}
```

### VS Code Settings
Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./bandruenv/Scripts/python.exe",
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=88"],
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "**/.pytest_cache": true
  },
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Pre-commit Configuration
Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3
        args: [--line-length=88]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

### Pytest Configuration
Create `pytest.ini`:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=app
    --cov=services
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    auth: Authentication tests
    slow: Slow running tests
```

### Black Configuration
Create `pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
  | migrations
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
include_trailing_comma = true
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]
known_first_party = ["app", "services", "database", "utils"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = [
    "alembic.*",
    "sqlalchemy.*",
    "fastapi.*",
    "pydantic.*",
    "uvicorn.*"
]
ignore_missing_imports = true
```

### Flake8 Configuration
Create `.flake8`:
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503, E501
exclude = 
    .git,
    __pycache__,
    .pytest_cache,
    .venv,
    bandruenv,
    migrations,
    build,
    dist
per-file-ignores =
    __init__.py:F401
    test_*.py:S101
```

### Docker Development
Create `docker-compose.dev.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - ./logs:/app/logs
    environment:
      - DEBUG=True
      - DATABASE_URL=sqlite:///./app.db
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: bandru_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Makefile for Common Tasks
Create `Makefile`:
```makefile
.PHONY: install dev test clean format lint type-check security

install:
	pip install -r requirements.txt
	pre-commit install

dev:
	python app/main.py

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ --cov=app --cov=services --cov-report=html

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build dist htmlcov .pytest_cache .coverage

format:
	black .
	isort .

lint:
	flake8 .
	pylint app services

type-check:
	mypy app services

security:
	bandit -r app services

setup-dev:
	python -m venv bandruenv
	bandruenv/Scripts/activate
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

docker-dev:
	docker-compose -f docker-compose.dev.yml up --build

docker-prod:
	docker-compose up --build

migration:
	alembic revision --autogenerate -m "$(message)"

migrate:
	alembic upgrade head

rollback:
	alembic downgrade -1

backup-db:
	python scripts/backup_database.py

restore-db:
	python scripts/restore_database.py $(file)
```

### Development Requirements
Create `requirements-dev.txt`:
```txt
# Development dependencies
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
pylint>=2.17.0
mypy>=1.3.0
bandit>=1.7.0
pre-commit>=3.3.0
httpx>=0.24.0  # For testing async clients
factory-boy>=3.2.0  # For test data generation
freezegun>=1.2.0  # For time-based testing
```

### GitHub Actions Workflow
Create `.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
    
    - name: Type check with mypy
      run: mypy app services
    
    - name: Test with pytest
      run: |
        pytest tests/ --cov=app --cov=services --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

### Development Scripts
Create development helper scripts in `scripts/` directory.

This comprehensive development setup ensures:
- ✅ Code quality and consistency
- ✅ Automated testing and coverage
- ✅ Type safety
- ✅ Security scanning
- ✅ Git hooks for quality gates
- ✅ Docker development environment
- ✅ CI/CD pipeline
- ✅ Easy onboarding for new developers

New developers can get started quickly with:
```bash
make setup-dev
make test
make dev
```
