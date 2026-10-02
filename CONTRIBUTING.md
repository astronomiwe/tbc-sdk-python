# Contributing

Create a focused branch, add tests for behavioural changes, and run:

```bash
python -m pip install -e '.[dev]'
pre-commit install
pytest
ruff check .
ruff format --check .
mypy
bandit -c pyproject.toml -r src
pip-audit
```

Build documentation before changing guides or examples:

```bash
python -m pip install -e '.[docs]'
mkdocs build --strict
```

Keep the public API typed and backward-compatible within a minor release. Do not add automatic retries to money-moving requests: callers must be able to reconcile an ambiguous result safely.

## Releases

`src/tbc_payments/__init__.py` is the single source of the package version. For a
release, update `__version__` and `CHANGELOG.md`, merge the changes, then create and
push a matching tag such as `v0.2.0`. A pushed `vX.Y.Z` tag builds, validates, and
publishes that exact version to PyPI through trusted publishing. TestPyPI publication
remains available from the manually dispatched release workflow.
