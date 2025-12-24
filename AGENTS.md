# Repository Guidelines

## Project Structure & Module Organization
- `app/`: application source code (PySide6 UI, use cases, domain logic, infra).
- `app/ui/`: UI shell and dialogs.
- `app/domain/`: business logic and pure calculations.
- `app/infra/`: DB, clients, config, logging, and secrets.
- `docs/`: product and engineering docs (requirements, setup, DB schema, workflow, TODO).
- `templates/`: seed and config templates.
- `data/`, `logs/`: runtime outputs (created locally; keep out of Git).

## Build, Test, and Development Commands
- `python -m venv .venv`: create local virtual environment.
- `.venv\Scripts\activate` (Windows) / `source .venv/bin/activate`: activate venv.
- `pip install PySide6 httpx pydantic keyring`: install baseline dependencies.
- `python -m app`: run the desktop app entrypoint.

## Coding Style & Naming Conventions
- Python 3.10+ compatible code.
- Indentation: 4 spaces, no tabs.
- Modules: `snake_case.py`; classes: `PascalCase`; functions/vars: `snake_case`.
- Keep UI logic in `app/ui/` and side effects in `app/infra/`.
- Favor small, focused modules; avoid cross-layer imports from `domain` to `infra`.

## Testing Guidelines
- Tests are not yet implemented. When added, place them under `tests/`.
- Name tests `test_*.py` and keep them close to the module under test.
- Prefer unit tests for domain logic; UI testing can be manual for MVP.

## Commit & Pull Request Guidelines
- No Git history is available in this folder, so there is no established commit message convention yet.
- If you add Git, prefer clear, scoped messages (e.g., `db: add schema init`).
- For pull requests, include a short summary, testing notes, and screenshots for UI changes.

## Security & Configuration Tips
- Store secrets in the OS keyring (see `docs/06_config_secrets.md`).
- Keep `config.json`, `data/`, and `logs/` out of version control.

## Architecture Notes
- Follow the layered design in `docs/02_architecture.md`.
- Do not block the UI thread with network I/O; use workers or threads.
