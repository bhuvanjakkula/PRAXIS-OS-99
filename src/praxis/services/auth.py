"""Authentication and Subscription service for PRAXIS OS.
Provides user registration (Sign Up), login (Sign In), 30-day automated trial tracking,
and subscription enforcement ($49 Starter, $499 Firm, $1,500 Enterprise).
"""
from __future__ import annotations
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

AUTH_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    mobile TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TEXT NOT NULL,
    trial_ends_at TEXT,
    subscription_status TEXT DEFAULT 'trial',
    subscription_plan TEXT
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_mobile ON users(mobile);

CREATE TABLE IF NOT EXISTS auth_sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON auth_sessions(user_id);
"""

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{6,15}$")

OWNER_EMAIL = "bhuvanjakkula@gmail.com"

PRICING_PLANS = {
    "starter": {
        "id": "starter",
        "name": "Starter",
        "price_usd": 49,
        "period": "month",
        "payment_url": "https://buy.stripe.com/test_3cIeV5fXt229e7L7CfcjS07",
        "badge": "Individual",
        "tagline": "For individual researchers, quantitative operators, and strategic analysts.",
        "features": [
            "Full Decision Canvas & Inquiry Engine",
            "Up to 25 Active Decision Models",
            "Newton, Dewey & Blake Analytical Engines",
            "Monte Carlo & Sensitivity Calculations",
            "Exportable Decision Dossiers (JSON / Markdown)",
            "Community & Standard Email Support"
        ]
    },
    "firm": {
        "id": "firm",
        "name": "Firm",
        "price_usd": 499,
        "period": "month",
        "payment_url": "https://buy.stripe.com/test_bJecMX26D229fbPg8LcjS08",
        "badge": "Most Popular",
        "tagline": "For boutique investment firms, advisory partnerships, and risk teams.",
        "features": [
            "Everything in Starter",
            "Unlimited Active Decision Models",
            "Full Cockpit Simulation & Replay Lab",
            "Maritime Coordination & AIS Telemetry",
            "IMF & World Bank Macroeconomic Lenses",
            "Priority Support & Dedicated Account Specialist",
            "Shared Team Workspace & Multi-User Governance"
        ]
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "price_usd": 1500,
        "period": "month",
        "payment_url": "https://buy.stripe.com/test_aFacMXfXt5eld3HaOrcjS09",
        "badge": "Institutional",
        "tagline": "For global financial institutions, regulatory bodies, and defense agencies.",
        "features": [
            "Everything in Firm",
            "Post-Quantum Cryptography (PQC) Key Signing",
            "Custom Telemetry Ingress & Real-Time Sensors",
            "Isolated PostgreSQL & Dedicated Tenant Hosting",
            "Custom ML & Quantitative Model Calibrations",
            "24/7 SLA Guarantee & On-Premises Airgap Option",
            "Executive Briefing & Strategic Advisory Sessions"
        ]
    }
}


def normalize_mobile(mobile: str) -> str:
    cleaned = re.sub(r"[\s\-\(\)\.]", "", mobile.strip())
    return cleaned


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return key.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return hmac.compare_digest(key.hex(), password_hash)


class TrialExpiredException(ValueError):
    """Raised when a user's 30-day free trial has ended and payment is required."""
    def __init__(self, message: str, user_id: str, email: str, trial_ends_at: str):
        super().__init__(message)
        self.user_id = user_id
        self.email = email
        self.trial_ends_at = trial_ends_at


class AuthService:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            conn.executescript(AUTH_SCHEMA)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(users)")
            cols = [row["name"] for row in cur.fetchall()]
            if "trial_ends_at" not in cols:
                cur.execute("ALTER TABLE users ADD COLUMN trial_ends_at TEXT")
            if "subscription_status" not in cols:
                cur.execute("ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'trial'")
            if "subscription_plan" not in cols:
                cur.execute("ALTER TABLE users ADD COLUMN subscription_plan TEXT")

            # Ensure owner account exists with permanent active enterprise access
            cur.execute("SELECT id, email FROM users WHERE email = ?", (OWNER_EMAIL,))
            owner = cur.fetchone()
            now = datetime.now(timezone.utc).isoformat()
            if not owner:
                owner_id = secrets.token_hex(16)
                pwd_hash, salt = hash_password(secrets.token_urlsafe(32))
                cur.execute(
                    "INSERT INTO users (id, full_name, email, mobile, password_hash, salt, created_at, trial_ends_at, subscription_status, subscription_plan) "
                    "VALUES (?, 'Operator', ?, '+1000000000', ?, ?, ?, NULL, 'active', 'enterprise')",
                    (owner_id, OWNER_EMAIL, pwd_hash, salt, now)
                )
            else:
                cur.execute(
                    "UPDATE users SET subscription_status = 'active', subscription_plan = 'enterprise', trial_ends_at = NULL WHERE email = ?",
                    (OWNER_EMAIL,)
                )
            conn.commit()
        finally:
            conn.close()

    def register(self, full_name: str, email: str, mobile: str, password: str) -> Dict[str, Any]:
        full_name = full_name.strip()
        if len(full_name) < 2:
            raise ValueError("Full name must be at least 2 characters.")

        email_norm = normalize_email(email)
        if not EMAIL_REGEX.match(email_norm):
            raise ValueError("Invalid email format. Please provide a valid email address.")

        mobile_norm = normalize_mobile(mobile)
        if not PHONE_REGEX.match(mobile_norm) or len(mobile_norm) < 7:
            raise ValueError("Invalid mobile number. Please provide a valid phone number (min 7 digits).")

        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")

        pwd_hash, salt = hash_password(password)
        user_id = secrets.token_hex(16)
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        
        is_owner = (email_norm == OWNER_EMAIL)
        trial_ends = None if is_owner else (now_dt + timedelta(days=30)).isoformat()
        sub_status = "active" if is_owner else "trial"
        sub_plan = "enterprise" if is_owner else None

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, email, mobile FROM users WHERE email = ? OR mobile = ?", (email_norm, mobile_norm))
            existing = cur.fetchone()
            if existing:
                if existing["email"] == email_norm:
                    raise ValueError("An account with this email address already exists.")
                if existing["mobile"] == mobile_norm:
                    raise ValueError("An account with this mobile number already exists.")

            cur.execute(
                "INSERT INTO users (id, full_name, email, mobile, password_hash, salt, created_at, trial_ends_at, subscription_status, subscription_plan) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, full_name, email_norm, mobile_norm, pwd_hash, salt, now, trial_ends, sub_status, sub_plan)
            )

            token = secrets.token_urlsafe(32)
            cur.execute(
                "INSERT INTO auth_sessions (token, user_id, created_at) VALUES (?, ?, ?)",
                (token, user_id, now)
            )
            conn.commit()
        finally:
            conn.close()

        return {
            "token": token,
            "user": {
                "id": user_id,
                "full_name": full_name,
                "email": email_norm,
                "mobile": mobile_norm,
                "created_at": now,
                "trial_ends_at": trial_ends,
                "subscription_status": sub_status,
                "subscription_plan": sub_plan,
                "days_remaining": 9999 if is_owner else 30
            },
            "message": "User registered successfully."
        }

    def login(self, identifier: str, password: str = "", bypass_expiry: bool = False) -> Dict[str, Any]:
        ident = identifier.strip()
        if not ident:
            raise ValueError("Please provide your Email ID or Mobile number.")

        email_cand = normalize_email(ident)
        mobile_cand = normalize_mobile(ident)
        is_owner = (email_cand == OWNER_EMAIL)

        # Non-owners require a password; owner can log in without password or with any password
        if not is_owner and not password:
            raise ValueError("Please provide your password.")

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, full_name, email, mobile, password_hash, salt, created_at, trial_ends_at, subscription_status, subscription_plan "
                "FROM users WHERE email = ? OR mobile = ?",
                (email_cand, mobile_cand)
            )
            user = cur.fetchone()
            
            # If owner is not in DB yet, auto-create
            if not user and is_owner:
                user_id = secrets.token_hex(16)
                pwd_hash, salt = hash_password(secrets.token_urlsafe(32))
                now = datetime.now(timezone.utc).isoformat()
                cur.execute(
                    "INSERT INTO users (id, full_name, email, mobile, password_hash, salt, created_at, trial_ends_at, subscription_status, subscription_plan) "
                    "VALUES (?, 'Operator', ?, '+1000000000', ?, ?, ?, NULL, 'active', 'enterprise')",
                    (user_id, OWNER_EMAIL, pwd_hash, salt, now)
                )
                conn.commit()
                cur.execute(
                    "SELECT id, full_name, email, mobile, password_hash, salt, created_at, trial_ends_at, subscription_status, subscription_plan "
                    "FROM users WHERE email = ?",
                    (OWNER_EMAIL,)
                )
                user = cur.fetchone()

            if not user:
                raise ValueError("No account found with that email or mobile number.")

            # Password check (skipped for owner)
            if not is_owner:
                if not verify_password(password, user["password_hash"], user["salt"]):
                    raise ValueError("Incorrect password. Please try again.")

            # Owner has lifetime enterprise access without paying
            if is_owner:
                status = "active"
                plan = "enterprise"
                days_left = 9999
                trial_ends_str = None
                cur.execute(
                    "UPDATE users SET subscription_status = 'active', subscription_plan = 'enterprise', trial_ends_at = NULL WHERE id = ?",
                    (user["id"],)
                )
                conn.commit()
            else:
                status = user["subscription_status"] or "trial"
                plan = user["subscription_plan"]
                trial_ends_str = user["trial_ends_at"]
                now_dt = datetime.now(timezone.utc)
                days_left = 30

                if trial_ends_str:
                    try:
                        trial_end_dt = datetime.fromisoformat(trial_ends_str)
                        diff = (trial_end_dt - now_dt).total_seconds()
                        days_left = max(0, int(diff // 86400))
                        if diff <= 0 and status != "active":
                            status = "expired"
                            cur.execute("UPDATE users SET subscription_status = 'expired' WHERE id = ?", (user["id"],))
                            conn.commit()
                    except Exception:
                        pass

                if status == "expired" and not bypass_expiry:
                    raise TrialExpiredException(
                        "Your 30-day free trial has expired. Please select a subscription plan (Starter $49, Firm $499, or Enterprise $1,500) to reactivate your workspace access.",
                        user_id=user["id"],
                        email=user["email"],
                        trial_ends_at=trial_ends_str or ""
                    )

            token = secrets.token_urlsafe(32)
            now = datetime.now(timezone.utc).isoformat()
            cur.execute(
                "INSERT INTO auth_sessions (token, user_id, created_at) VALUES (?, ?, ?)",
                (token, user["id"], now)
            )
            conn.commit()
        finally:
            conn.close()

        return {
            "token": token,
            "user": {
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "mobile": user["mobile"],
                "created_at": user["created_at"],
                "trial_ends_at": trial_ends_str,
                "subscription_status": status,
                "subscription_plan": plan,
                "days_remaining": days_left
            },
            "message": "Signed in successfully."
        }

    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        if not token:
            return None
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT u.id, u.full_name, u.email, u.mobile, u.created_at, u.trial_ends_at, u.subscription_status, u.subscription_plan "
                "FROM auth_sessions s "
                "JOIN users u ON s.user_id = u.id "
                "WHERE s.token = ?",
                (token,)
            )
            row = cur.fetchone()
            if not row:
                return None

            is_owner = (row["email"] == OWNER_EMAIL)
            status = "active" if is_owner else (row["subscription_status"] or "trial")
            plan = "enterprise" if is_owner else row["subscription_plan"]
            trial_ends_str = None if is_owner else row["trial_ends_at"]
            days_left = 9999 if is_owner else 30

            if not is_owner and trial_ends_str:
                try:
                    trial_end_dt = datetime.fromisoformat(trial_ends_str)
                    diff = (trial_end_dt - datetime.now(timezone.utc)).total_seconds()
                    days_left = max(0, int(diff // 86400))
                    if diff <= 0 and status != "active":
                        status = "expired"
                except Exception:
                    pass

            return {
                "id": row["id"],
                "full_name": row["full_name"],
                "email": row["email"],
                "mobile": row["mobile"],
                "created_at": row["created_at"],
                "trial_ends_at": trial_ends_str,
                "subscription_status": status,
                "subscription_plan": plan,
                "days_remaining": days_left
            }
        finally:
            conn.close()

    def activate_subscription(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        plan_id = plan_id.lower().strip()
        if plan_id not in PRICING_PLANS:
            raise ValueError(f"Invalid plan '{plan_id}'. Choose from: starter, firm, enterprise.")

        plan_info = PRICING_PLANS[plan_id]
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, email, full_name FROM users WHERE id = ?", (user_id,))
            user = cur.fetchone()
            if not user:
                raise ValueError("User not found.")

            cur.execute(
                "UPDATE users SET subscription_status = 'active', subscription_plan = ? WHERE id = ?",
                (plan_id, user_id)
            )
            conn.commit()
        finally:
            conn.close()

        return {
            "success": True,
            "user_id": user_id,
            "subscription_plan": plan_id,
            "plan_name": plan_info["name"],
            "price_usd": plan_info["price_usd"],
            "subscription_status": "active",
            "message": f"Successfully subscribed to the {plan_info['name']} plan (${plan_info['price_usd']}/month). Access renewed."
        }

    def logout(self, token: str):
        if not token:
            return
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
            conn.commit()
        finally:
            conn.close()
