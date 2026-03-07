# Workspace Boundaries

## Purpose

This document defines which directories are source code and which directories are runtime/generated data.

The goal is to keep development work focused on canonical source paths and avoid mixing generated artifacts into analysis, debugging, or future version control.

## Canonical Source Directories

These directories should be treated as primary source code and documentation:

- `agents/`
- `api/app/`
- `config/`
- `docs/`
- `scripts/`
- `tests/`
- `utils/`
- `web/src/`
- `README.md`
- `requirements.txt`
- `web/package.json`

## Runtime / Generated Directories

These directories are not canonical source and should not be relied on as the source of truth:

- `outputs/`
- `api/outputs/`
- `temp_extract/`
- `api/temp_extract/`
- `logs/`
- `uploads/`
- `inputs/`
- `tests/outputs/`
- `web/node_modules/`
- `venv/`
- `__pycache__/`

## Working Rules

- Prefer reading and editing files only from canonical source directories.
- Treat files under runtime/generated directories as disposable unless explicitly needed for debugging.
- Do not use intermediate JSON or extracted temp projects as the basis for code changes unless the task specifically requires artifact inspection.
- Recreate generated outputs from source whenever possible instead of editing them directly.

## Cleanup Policy

Low-risk generated artifacts that can be deleted and recreated:

- `outputs/`
- `api/outputs/`
- `temp_extract/`
- `api/temp_extract/`
- `logs/`
- `__pycache__/`

Usually keep unless explicitly requested:

- `inputs/`
- `uploads/`
- `venv/`
- `web/node_modules/`

## Search Hygiene

Root `.gitignore` and `.rgignore` are used to reduce noise from runtime directories.

When searching the project:

- default to canonical source paths first
- avoid using generated artifacts to infer intended behavior

