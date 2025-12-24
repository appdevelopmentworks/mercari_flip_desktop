from __future__ import annotations

SERVICE_NAME = "mercari_flip_desktop"


def _require_keyring():
    try:
        import keyring  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("keyring is not installed") from exc
    return keyring


def get_secret(key: str) -> str | None:
    keyring = _require_keyring()
    return keyring.get_password(SERVICE_NAME, key)


def set_secret(key: str, value: str) -> None:
    keyring = _require_keyring()
    keyring.set_password(SERVICE_NAME, key, value)


def delete_secret(key: str) -> None:
    keyring = _require_keyring()
    keyring.delete_password(SERVICE_NAME, key)
