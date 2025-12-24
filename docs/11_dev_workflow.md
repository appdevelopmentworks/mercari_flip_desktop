# Development Workflow (Bootstrap to Smoke Test)

## Goal
- Reduce guesswork during the first implementation pass.
- Clarify where config, data, and logs should live for local development.

## Initial Bootstrap
1. Set up Python as described in `docs/01_setup.md`.
2. Create the `app/` structure from `docs/02_architecture.md`.
3. Create `data/` and `logs/` directories (or create them on app start).
4. Place templates (and keep them out of Git where needed):
   - `templates/config.template.json` -> `config.json`
   - `templates/shipping_rules.seed.csv` -> `data/shipping_rules.csv`
   - `templates/items.import.template.csv` -> `data/items.import.csv`
5. Smoke test:
   - `python -m app` launches.
   - Config loads without error.

## Recommended Locations
- Non-secret config: `./config.json`
- Secrets: `keyring` (see `docs/06_config_secrets.md`)
- SQLite DB: `./data/app.db`
- Shipping rules: `./data/shipping_rules.csv`
- Logs: `./logs/app.log`

## Minimum Checkpoints
- UI launches and is interactive.
- DB can be created/opened.
- Shipping rules can be loaded.
- Refresh flow completes with connector stubs.

## Implementation Notes
- Use `pathlib.Path` for repo-root relative paths.
- Do not block the UI thread for network calls.
- Log API errors and rate-limit responses.
