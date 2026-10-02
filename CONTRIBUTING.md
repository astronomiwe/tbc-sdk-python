# Contributing

Thank you for improving `tbc-payments`. Keep each pull request focused: one bug fix,
endpoint, model change, or documentation improvement at a time.

## Set up a development checkout

Fork the repository, create a branch from `master`, then install the project with its
development dependencies:

```bash
python -m pip install -e '.[dev]'
pre-commit install
pytest
ruff check .
ruff format --check .
mypy
bandit -c pyproject.toml -r src
pip-audit
zizmor .github/workflows
```

`pre-commit` runs the relevant fast checks before each commit. Run `pre-commit run
--all-files` after changing tooling or workflows.

## Change checklist

- Add or update a test for every behaviour change. Tests must not use real TBC credentials.
- Keep public models and methods typed. Preserve backward compatibility in patch releases.
- Update the relevant guide and runnable example when an API change affects users.
- Add a concise entry under `Unreleased` in `CHANGELOG.md` for user-visible changes.
- Do not add automatic retries to money-moving requests: callers must be able to reconcile
  an ambiguous result safely.

Open a pull request using the provided template. CI must pass on all supported Python
versions before merge.

Build documentation before changing guides or examples:

```bash
python -m pip install -e '.[docs]'
mkdocs build --strict
```

## Releases

`src/tbc_payments/__init__.py` is the single source of the package version. A maintainer
prepares a release as follows:

1. Update `__version__` and move the relevant entries from `Unreleased` into a dated
   version section in `CHANGELOG.md`.
2. Run `pre-commit run --all-files`, `pytest`, `mypy`, `pip-audit`, and
   `mkdocs build --strict`.
3. Merge the release commit to `master`, then create and push the matching tag, for
   example `v0.3.1`.
4. Watch the **Release** workflow. It builds, validates, publishes through PyPI Trusted
   Publishing, and installs the package back from PyPI in a clean environment.

TestPyPI publication is available from the manually dispatched Release workflow before
publishing a new package for the first time.
