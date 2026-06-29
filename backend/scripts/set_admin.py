"""Grant (or revoke) admin rights for a user by email.

Users are provisioned on first sign-in with ``is_admin=False``; this is the
supported way to promote one. Run with:

    python -m scripts.set_admin user@example.com           # grant
    python -m scripts.set_admin user@example.com --revoke  # revoke
"""

from __future__ import annotations

import argparse

from app.infrastructure.db.session import SessionLocal
from app.infrastructure.models.models import User
from sqlalchemy import select


def set_admin(email: str, *, is_admin: bool) -> None:
    session = SessionLocal()
    try:
        user = session.scalars(select(User).where(User.email == email)).first()
        if user is None:
            print(f"No user found with email {email!r}. They must sign in at least once first.")
            return
        user.is_admin = is_admin
        session.commit()
        print(f"User {email!r} is_admin set to {is_admin}.")
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grant or revoke admin rights for a user.")
    parser.add_argument("email", help="Email of the user to update")
    parser.add_argument("--revoke", action="store_true", help="Revoke admin instead of granting")
    args = parser.parse_args()
    set_admin(args.email, is_admin=not args.revoke)
