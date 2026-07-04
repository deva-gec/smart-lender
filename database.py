"""SQLite database for users and loan application records."""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "smart_lender.db")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firebase_uid TEXT UNIQUE NOT NULL,
                phone TEXT,
                email TEXT,
                display_name TEXT,
                photo_url TEXT,
                auth_provider TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS loan_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                gender TEXT NOT NULL,
                married TEXT NOT NULL,
                education TEXT NOT NULL,
                self_employed TEXT NOT NULL,
                applicant_income REAL NOT NULL,
                loan_amount REAL NOT NULL,
                loan_amount_term INTEGER NOT NULL,
                credit_history INTEGER NOT NULL,
                property_area TEXT NOT NULL,
                prediction TEXT NOT NULL,
                raw_prediction TEXT NOT NULL,
                confidence REAL NOT NULL,
                approval_probability REAL NOT NULL,
                default_probability REAL NOT NULL,
                risk_level TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE INDEX IF NOT EXISTS idx_applications_user
                ON loan_applications(user_id);
            """
        )


def upsert_user(
    firebase_uid: str,
    auth_provider: str,
    phone: str | None = None,
    email: str | None = None,
    display_name: str | None = None,
    photo_url: str | None = None,
) -> dict:
    now = _utc_now()
    with get_db() as conn:
        existing = conn.execute(
            "SELECT * FROM users WHERE firebase_uid = ?", (firebase_uid,)
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE users SET phone = ?, email = ?, display_name = ?,
                photo_url = ?, auth_provider = ?, last_login_at = ?
                WHERE firebase_uid = ?
                """,
                (phone, email, display_name, photo_url, auth_provider, now, firebase_uid),
            )
            user = conn.execute(
                "SELECT * FROM users WHERE firebase_uid = ?", (firebase_uid,)
            ).fetchone()
        else:
            cursor = conn.execute(
                """
                INSERT INTO users (
                    firebase_uid, phone, email, display_name, photo_url,
                    auth_provider, created_at, last_login_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    firebase_uid,
                    phone,
                    email,
                    display_name,
                    photo_url,
                    auth_provider,
                    now,
                    now,
                ),
            )
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()

    return dict(user)


def get_user_by_id(user_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def save_application(user_id: int, form_data: dict, result: dict) -> int:
    applicant = result["applicant"]
    now = _utc_now()
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO loan_applications (
                user_id, gender, married, education, self_employed,
                applicant_income, loan_amount, loan_amount_term, credit_history,
                property_area, prediction, raw_prediction, confidence,
                approval_probability, default_probability, risk_level,
                recommendation, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                applicant["Gender"],
                applicant["Married"],
                applicant["Education"],
                applicant["Self_Employed"],
                applicant["ApplicantIncome"],
                applicant["LoanAmount"],
                applicant["Loan_Amount_Term"],
                applicant["Credit_History"],
                applicant["Property_Area"],
                result["prediction"],
                result["raw_prediction"],
                result["confidence"],
                result["approval_probability"],
                result["default_probability"],
                result["risk_level"],
                result["recommendation"],
                now,
            ),
        )
        return cursor.lastrowid


def get_user_applications(user_id: int, limit: int = 50) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM loan_applications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def export_user_data(user_id: int) -> dict:
    user = get_user_by_id(user_id)
    applications = get_user_applications(user_id, limit=1000)
    return {"user": user, "applications": applications, "exported_at": _utc_now()}
