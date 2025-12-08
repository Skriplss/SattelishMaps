# Contributing to SattelishMaps

Thank you for your interest in contributing! We welcome improvements, bug fixes, and new features.

## 🛠️ Development Setup

1. **Python Setup**
   Ensure you have Python 3.11+ installed.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Code Style**
   We use `ruff` for linting and formatting.
   ```bash
   # Run linter
   ruff check .
   
   # Format code
   ruff format .
   ```

## 🔀 Git Workflow

We follow a simplified feature-branch workflow.

1. **Fork & Clone**
2. **Create a Branch**
   Use descriptive names:
   - `feat/new-layer-control`
   - `fix/scheduler-timeout`
   - `docs/update-readme`
3. **Commit Changes**
   We encourage [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: add moisture index calculation`
   - `fix: resolve db connection retry issue`
4. **Push & Pull Request**
   Push to your fork and open a PR against `main`.

## 🧪 Testing

Please ensure all tests pass before submitting a PR.
```bash
pytest
```

## 📋 Pull Request Process

1. Update the `README.md` or documentation with details of changes if applicable.
2. The PR will be reviewed by a maintainer.
3. Once approved, it will be merged.
