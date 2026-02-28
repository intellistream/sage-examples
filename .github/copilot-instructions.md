# SAGE Examples Copilot Instructions

## Scope
- Repository: `intellistream/sage-examples` (examples + app entry scripts, not SAGE core).
- Read docs first: `README.md`, `tutorials/README.md`, `tutorials/QUICK_START.md`, `examples/README.md`.

## Critical rules
- Runtime direction: Flownet-first; do not add new `ray` imports/dependencies.
- Do not create new local virtual environments (`venv`/`.venv`); use the existing configured Python environment.
- In conda environments, use `python -m pip` (never plain `pip`).
- Do not rely on manual install commands for permanent deps; declare in `pyproject.toml`/`requirements.txt`.
- No silent fallback logic; fail fast with actionable errors.
- Do not re-add SAGE core internals here; depend on published `isage-*` packages.

## Dependency and setup
- If work depends on SAGE core behavior, ensure SAGE dev env is prepared via `./quickstart.sh --dev --yes` in `SAGE/`.
- Keep dependency changes explicit and versioned in this repo files.

## Workflow
1. Confirm target area (`examples/`, `tutorials/`, or `sage-apps/`).
2. Implement minimal repo-local change.
3. Run relevant tests/linters and update nearby README when behavior changes.

## High-signal paths
- `examples/`, `tutorials/`, `sage-apps/`, `requirements.txt`, `README.md`.

## Polyrepo coordination (mandatory)

- This repository is an independent SAGE sub-repository and is developed/released independently.
- Do not assume sibling source directories exist locally in `intellistream/SAGE`.
- For cross-repo rollout, publish this repo/package first, then bump the version pin in `SAGE/packages/sage/pyproject.toml` when applicable.
- Do not add local editable installs of other SAGE sub-packages in setup scripts or docs.
