import os


def get_api_config() -> tuple[str, str, str]:
    api_key = os.getenv("API_KEY", "").strip()
    base_url = os.getenv("BASE_URL", "").strip()
    model = os.getenv("MODEL", "").strip()

    missing = []
    if not api_key:
        missing.append("API_KEY")
    if not base_url:
        missing.append("BASE_URL")
    if not model:
        missing.append("MODEL")

    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variables: {missing_text}. "
            "Please set API_KEY, BASE_URL, MODEL before running."
        )
    return api_key, base_url, model


def normalize_openai_base_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return base
    return f"{base}/v1"


def build_chat_completions_url(base_url: str) -> str:
    return f"{normalize_openai_base_url(base_url)}/chat/completions"
