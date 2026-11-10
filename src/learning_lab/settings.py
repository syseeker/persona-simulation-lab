"""Runtime configuration. Secrets stay outside serialized settings."""

from pathlib import Path
import os

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


def load_environment() -> None:
    load_dotenv(ROOT / ".env", override=False)


def model_id(role: str = "assistant") -> str:
    load_environment()
    value = (
        os.getenv(f"NIM_{role.upper()}_MODEL")
        or os.getenv("NIM_MODEL")
        or (
            "nvidia/nemotron-3.5-lightning-30b-a3b"
            if role == "assistant"
            else "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
        )
    )
    return value


def base_url() -> str:
    load_environment()
    return os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/")
