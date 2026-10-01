# Contributing

Create a focused branch, add tests for behavioural changes, and run:

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```

Keep the public API typed and backward-compatible within a minor release. Do not add automatic retries to money-moving requests: callers must be able to reconcile an ambiguous result safely.
