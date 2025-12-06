# Development Guide

Посібник для розробників SattelishMaps.

## Початок роботи

1. Клонуйте репозиторій
2. Налаштуйте локальне середовище ([Installation](../getting-started/installation.md))
3. Ознайомтеся з [Git Workflow](git-workflow.md)
4. Прочитайте [Code Style](code-style.md)

## Структура розробки

### Backend Development

```bash
# Активувати venv
source .venv/bin/activate

# Встановити dev залежності
pip install ruff mypy pytest pytest-cov

# Запустити backend
cd backend
uvicorn app:app --reload
```

### Frontend Development

```bash
# Запустити dev сервер
cd frontend
python -m http.server 3000
```

## Code Quality

### Linting (Ruff)

```bash
# Check
ruff check backend/

# Fix
ruff check --fix backend/
```

### Type Checking (Mypy)

```bash
mypy backend/ --strict
```

### Testing (Pytest)

```bash
pytest tests/ -v --cov=backend
```

## Git Workflow

Дотримуйтесь [Conventional Commits](git-workflow.md):

```bash
# Feature
git checkout -b feat/new-feature
git commit -m "feat: add new feature"

# Fix
git checkout -b fix/bug-fix
git commit -m "fix: resolve bug"
```

## Детальна документація

- [Git Workflow](git-workflow.md) - Conventional Commits
- [Code Style](code-style.md) - Ruff, Mypy, Docstrings
- [Testing](testing.md) - Pytest
- [Contributing](contributing.md) - Як допомогти
- [Troubleshooting](troubleshooting.md) - Вирішення проблем
