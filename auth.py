"""Firebase authentication and session helpers."""

import os
from functools import wraps

from flask import jsonify, redirect, request, session, url_for

_firebase_initialized = False


def init_firebase() -> bool:
    global _firebase_initialized
    if _firebase_initialized:
        return True

    service_account = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
    if not service_account or not os.path.exists(service_account):
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials

        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account)
            firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        return True
    except Exception:
        return False


def verify_firebase_token(id_token: str) -> dict:
    if not init_firebase():
        raise RuntimeError(
            "Firebase is not configured. Add FIREBASE_SERVICE_ACCOUNT_PATH to .env"
        )

    from firebase_admin import auth

    decoded = auth.verify_id_token(id_token, check_revoked=True)
    return decoded


def login_user(user: dict) -> None:
    session["user_id"] = user["id"]
    session["firebase_uid"] = user["firebase_uid"]
    session["display_name"] = user.get("display_name") or user.get("phone") or user.get("email")
    session.permanent = True


def logout_user() -> None:
    session.clear()


def current_user_id() -> int | None:
    return session.get("user_id")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user_id():
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped
