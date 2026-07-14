"""Authentication primitives: Firebase ID-token verification.

In Sprint 0 the verifier runs in *stub mode* (``AUTH_STUB_ENABLED=true``) and
returns a fixed development identity without contacting Firebase. The real
verification path via ``firebase-admin`` is wired but only exercised once stub
mode is disabled (Sprint 1+).
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_STUB_IDENTITY_UID = "stub-uid"
_STUB_IDENTITY_EMAIL = "dev@codepath.local"

# Lazily initialized firebase-admin app, created only when real verification is
# requested. Kept module-level so we initialize the SDK at most once.
_firebase_app = None


@dataclass(frozen=True)
class Identity:
    """The authenticated principal extracted from a verified token."""

    uid: str
    email: str | None = None
    is_admin: bool = False


def _stub_identity() -> Identity:
    return Identity(uid=_STUB_IDENTITY_UID, email=_STUB_IDENTITY_EMAIL, is_admin=False)


def _ensure_firebase(settings: Settings):
    """Initialize firebase-admin once, using the configured credentials."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    import firebase_admin
    from firebase_admin import credentials

    if settings.firebase_credentials_file:
        cred = credentials.Certificate(settings.firebase_credentials_file)
    else:
        # Application Default Credentials (e.g. GCP runtime).
        cred = credentials.ApplicationDefault()

    options = {}
    if settings.firebase_project_id:
        options["projectId"] = settings.firebase_project_id

    _firebase_app = firebase_admin.initialize_app(cred, options or None)
    return _firebase_app


def verify_token(token: str | None, settings: Settings) -> Identity:
    """Verify a Firebase ID token and return the resulting :class:`Identity`.

    Raises ``HTTPException(401)`` when a real token is missing or invalid.
    In stub mode a development identity is returned regardless of ``token``.
    """
    if settings.auth_stub_enabled:
        return _stub_identity()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from firebase_admin import auth as firebase_auth

    try:
        _ensure_firebase(settings)
        # Tolerate small clock skew between this host and Firebase (a token can
        # otherwise be rejected as "used too early" right after sign-in).
        decoded = firebase_auth.verify_id_token(token, clock_skew_seconds=10)
    except Exception as exc:  # noqa: BLE001 - surface any verification failure as 401
        logger.warning("Token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return Identity(
        uid=decoded["uid"],
        email=decoded.get("email"),
        is_admin=bool(decoded.get("admin", False)),
    )

def delete_firebase_user(uid: str, settings: Settings) -> bool:
    """Best-effort deletion of the Firebase Auth account (no-op in stub mode).

    Returns whether the Firebase user was deleted. Failures are logged and
    swallowed — the app account is the source of truth and is deleted anyway.
    """
    if settings.auth_stub_enabled:
        return False
    try:
        from firebase_admin import auth as fb_auth

        _ensure_firebase(settings)
        fb_auth.delete_user(uid)
        return True
    except Exception as exc:  # noqa: BLE001 - best effort only
        logger.warning("Firebase user deletion failed for %s: %s", uid, exc)
        return False
