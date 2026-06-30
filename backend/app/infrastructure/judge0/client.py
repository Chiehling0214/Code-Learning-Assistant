"""Judge0 HTTP client.

Wraps the Judge0 REST API for running source code against stdin. Normalizes the
response into a small dict and raises :class:`Judge0Error` on any transport or
configuration problem so callers can degrade gracefully.
"""

from __future__ import annotations

import httpx

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Maps our language slugs to Judge0 CE language ids. Extend as languages are
# added. (Ids per the Judge0 CE language list.)
LANGUAGE_IDS: dict[str, int] = {
    "python": 71,  # Python 3.8
    "javascript": 63,  # Node.js
    "typescript": 74,
    "c": 50,  # GCC
    "cpp": 54,  # G++
    "java": 62,
    "go": 60,
    "ruby": 72,
}


class Judge0Error(RuntimeError):
    """Raised when Judge0 is unreachable, misconfigured, or errors out."""


class Judge0Client:
    """Thin synchronous client for a Judge0 instance.

    Supports two backends, selected automatically from settings:

    * **RapidAPI** (when ``judge0_rapidapi_key`` is set) — targets the hosted
      Judge0 CE endpoint with RapidAPI headers. No local containers required.
    * **Self-hosted** (otherwise) — targets ``judge0_url`` with an optional
      ``X-Auth-Token``.

    Switching from RapidAPI to a local instance later is just an env change:
    clear ``JUDGE0_RAPIDAPI_KEY`` and point ``JUDGE0_URL`` at the local Judge0.
    """

    def __init__(self, settings: Settings) -> None:
        self._timeout = settings.judge0_timeout
        self._headers: dict[str, str] = {}

        if settings.judge0_rapidapi_key:
            host = settings.judge0_rapidapi_host
            self._url = f"https://{host}"
            self._headers.update(
                {
                    "X-RapidAPI-Key": settings.judge0_rapidapi_key,
                    "X-RapidAPI-Host": host,
                }
            )
        else:
            self._url = settings.judge0_url.rstrip("/")
            if settings.judge0_auth_token:
                self._headers["X-Auth-Token"] = settings.judge0_auth_token

    def execute(self, source_code: str, language: str, stdin: str = "") -> dict:
        """Run ``source_code`` once and return a normalized result dict.

        Keys: ``stdout``, ``stderr``, ``compile_output``, ``status_id``,
        ``status`` (description), ``time``, ``memory``.
        """
        language_id = LANGUAGE_IDS.get(language)
        if language_id is None:
            raise Judge0Error(f"Unsupported language: {language!r}")

        payload = {
            "source_code": source_code,
            "language_id": language_id,
            "stdin": stdin,
        }
        url = f"{self._url}/submissions?base64_encoded=false&wait=true"
        try:
            response = httpx.post(
                url, json=payload, headers=self._headers, timeout=self._timeout
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Judge0 execution failed: %s", exc)
            raise Judge0Error(f"Judge0 request failed: {exc}") from exc

        status = data.get("status") or {}
        return {
            "stdout": data.get("stdout") or "",
            "stderr": data.get("stderr") or "",
            "compile_output": data.get("compile_output"),
            "status_id": status.get("id"),
            "status": status.get("description"),
            "time": data.get("time"),
            "memory": data.get("memory"),
        }
