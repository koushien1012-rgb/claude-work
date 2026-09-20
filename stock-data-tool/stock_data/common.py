import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class MissingAPIKeyError(RuntimeError):
    pass


def get_api_key(env_var: str) -> str:
    key = os.environ.get(env_var, "").strip()
    if not key:
        raise MissingAPIKeyError(
            f"{env_var} is not set. Add it to the .env file in the project root."
        )
    return key


def get_env(env_var: str, default: str | None = None) -> str | None:
    value = os.environ.get(env_var, "").strip()
    return value or default


REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]
