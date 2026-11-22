"""Authentication and Subscription service for PRAXIS OS.
Provides user registration (Sign Up), login (Sign In), 30-day automated trial tracking,
and technology-aligned subscription tiers (Core Studio, APEX Intelligence,
Command & Sovereign, and Quantum Sovereign Dedicated).
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import sqlite3
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import quote

SUPPORT_EMAIL = "contact@apolloaiglobalcompany.com"
RESET_TOKEN_TTL_MINUTES = 15
RESET_SECRET = os.getenv("PRAXIS_RESET_SECRET", "praxis-os-apollo-reset-key-v1").encode("utf-8")

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

CREATE TABLE IF NOT EXISTS password_resets (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    email TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_resets_email ON password_resets(email);
"""

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{6,15}$")

OWNER_EMAIL = "bhuvanjakkula@gmail.com"

PRICING_PLANS = {
    "core_studio": {
        "id": "core_studio",
        "name": "Core Studio",
        "price_usd": 99,
        "annual_price_usd": 79,
        "period": "month",
        "payment_url": "https://buy.stripe.com/fZu00b41gfWtbTh58a2oE0z",
        "badge": "Individual Strategist",
        "tagline": "For solo founders, strategic analysts, and quantitative researchers.",
        "features": [
            "Decision Canvas & 5-Engine Structured Inquiry",
            "Up to 50 Active Decision Models",
            "Monte Carlo, Causal & Sensitivity Simulation",
            "AI Solutions (3-Pass Grounded Synthesis)",
            "Decision Dossier Exports (JSON / Print PDF)",
            "Standard Email Support"
        ]
    },
    "apex_intelligence": {
        "id": "apex_intelligence",
        "name": "APEX Intelligence",
        "price_usd": 349,
        "annual_price_usd": 279,
        "period": "month",
        "payment_url": "https://buy.stripe.com/bJefZ99lA25Df5t58a2oE0y",
        "badge": "Most Popular · APEX Engine",
        "popular": True,
        "tagline": "Unlocks the PRAXIS APEX Kernel: Game Theory, Bayesian VOI & Fat-Tail CVaR.",
        "features": [
            "Everything in Core Studio + Unlimited Models",
            "APEX Multi-Agent Nash & Minimax Regret Solver",
            "Bayesian EVPI / EVSI Value-of-Information Engine",
            "Fat-Tail CVaR (95%) & Ruin Stress Testing",
            "SHA-256 Merkle Cryptographic Decision Seals",
            "Executive Cockpits (CEO, CFO, CTO & CMO)",
            "Up to 5 Team Operator Seats"
        ]
    },
    "command_sovereign": {
        "id": "command_sovereign",
        "name": "Command & Sovereign",
        "price_usd": 1250,
        "annual_price_usd": 999,
        "period": "month",
        "payment_url": "https://buy.stripe.com/8x24gr41geSp6yX1VY2oE0x",
        "badge": "Institutional & Macro",
        "tagline": "For investment funds, policy ministries, aviation/maritime ops, and enterprise risk teams.",
        "features": [
            "Everything in APEX Intelligence + Unlimited Seats",
            "IMF, World Bank & 217-Country National Strategy",
            "Policy Scorecard & Multi-Criteria Appraisal",
            "Aviation Security & Maritime Fusion Replay Labs",
            "Enterprise Source-Change Impact Audit Ledger",
            "Priority SLA & Dedicated Onboarding Specialist"
        ]
    },
    "quantum_sovereign": {
        "id": "quantum_sovereign",
        "name": "Quantum Sovereign Dedicated",
        "price_usd": 3900,
        "annual_price_usd": 3120,
        "period": "month",
        "payment_url": "https://buy.stripe.com/dRmeV50P4h0x1eD1VY2oE0w",
        "badge": "Dedicated · Airgap Ready",
        "tagline": "For central banks, defense agencies, and regulated global financial institutions.",
        "features": [
            "Everything in Command & Sovereign",
            "Dedicated Isolated Tenant & PostgreSQL Cluster",
            "Post-Quantum Cryptographic (PQC) Audit Signing",
            "Custom Real-Time Telemetry & Sensor Ingress",
            "Custom Quantitative & APEX Kernel Calibration",
            "24/7 Executive War-Room SLA & Airgap Option"
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

        account_proof = self._sign_account_proof({
            "id": user_id,
            "full_name": full_name,
            "email": email_norm,
            "mobile": mobile_norm,
            "password_hash": pwd_hash,
            "salt": salt,
            "created_at": now,
            "trial_ends_at": trial_ends,
            "subscription_status": sub_status,
            "subscription_plan": sub_plan,
            "updated_at": now,
        })

        return {
            "token": token,
            "account_proof": account_proof,
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

    def login(self, identifier: str, password: str = "", bypass_expiry: bool = False, account_proof: Optional[str] = None) -> Dict[str, Any]:
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
            self._rehydrate_from_proof(conn, account_proof)
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
            valid = ", ".join(PRICING_PLANS.keys())
            raise ValueError(f"Invalid plan '{plan_id}'. Choose from: {valid}.")

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

    def _sign_reset_token(self, email_norm: str, expires_ts: int) -> str:
        nonce = secrets.token_hex(8)
        body = f"{email_norm}|{expires_ts}|{nonce}".encode("utf-8")
        b64 = base64.urlsafe_b64encode(body).decode("ascii").rstrip("=")
        sig = hmac.new(RESET_SECRET, b64.encode("ascii"), hashlib.sha256).hexdigest()[:32]
        return f"{b64}.{sig}"

    def _verify_signed_reset_token(self, token: str, email_norm: str) -> bool:
        try:
            b64, sig = token.strip().split(".", 1)
            expected = hmac.new(RESET_SECRET, b64.encode("ascii"), hashlib.sha256).hexdigest()[:32]
            if not hmac.compare_digest(sig, expected):
                return False
            padded = b64 + "=" * (-len(b64) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
            tok_email, exp_str, _nonce = decoded.split("|", 2)
            if tok_email != email_norm:
                return False
            return int(exp_str) >= int(datetime.now(timezone.utc).timestamp())
        except Exception:
            return False

    def _try_send_reset_email(self, recipient: str, full_name: str, reset_link: str) -> bool:
        smtp_host = os.getenv("SMTP_HOST")
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        if not (smtp_host and smtp_user and smtp_pass):
            return False
        try:
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            msg = EmailMessage()
            msg["Subject"] = "PRAXIS OS — Password Reset Update Link"
            msg["From"] = os.getenv("SMTP_FROM", SUPPORT_EMAIL)
            msg["To"] = recipient
            msg.set_content(
                f"Hello {full_name},\n\n"
                f"We received a request to reset your PRAXIS OS password.\n"
                f"Use the update link below within {RESET_TOKEN_TTL_MINUTES} minutes to set a new password:\n\n"
                f"{reset_link}\n\n"
                f"If you need assistance, contact Customer Support at {SUPPORT_EMAIL}.\n"
            )
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return True
        except Exception:
            return False

    def _sign_account_proof(self, data: Dict[str, Any]) -> str:
        raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        b64 = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
        sig = hmac.new(RESET_SECRET, b64.encode("ascii"), hashlib.sha256).hexdigest()[:32]
        return f"{b64}.{sig}"

    def _rehydrate_from_proof(self, conn: sqlite3.Connection, account_proof: Optional[str]) -> None:
        if not account_proof or "." not in account_proof:
            return
        try:
            b64, sig = account_proof.strip().split(".", 1)
            expected = hmac.new(RESET_SECRET, b64.encode("ascii"), hashlib.sha256).hexdigest()[:32]
            if not hmac.compare_digest(sig, expected):
                return
            padded = b64 + "=" * (-len(b64) % 4)
            data = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
            email = normalize_email(str(data.get("email", "")))
            if not email or not data.get("id") or not data.get("password_hash") or not data.get("salt"):
                return
            cur = conn.cursor()
            cur.execute("SELECT id, password_hash, salt FROM users WHERE email = ?", (email,))
            existing = cur.fetchone()
            if not existing:
                cur.execute(
                    "INSERT OR IGNORE INTO users (id, full_name, email, mobile, password_hash, salt, created_at, trial_ends_at, subscription_status, subscription_plan) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        data["id"],
                        data.get("full_name", "User"),
                        email,
                        data.get("mobile", ""),
                        data["password_hash"],
                        data["salt"],
                        data.get("created_at", datetime.now(timezone.utc).isoformat()),
                        data.get("trial_ends_at"),
                        data.get("subscription_status", "trial"),
                        data.get("subscription_plan"),
                    ),
                )
            elif existing["password_hash"] != data["password_hash"]:
                # Keep password hash in sync across cold serverless containers after password reset
                cur.execute(
                    "UPDATE users SET password_hash = ?, salt = ? WHERE email = ?",
                    (data["password_hash"], data["salt"], email),
                )
            conn.commit()
        except Exception:
            return

    def request_password_reset(self, email: str, base_url: str = "", account_proof: Optional[str] = None) -> Dict[str, Any]:
        email_norm = normalize_email(email)
        if not EMAIL_REGEX.match(email_norm):
            raise ValueError("Please enter a valid registered email ID.")

        conn = self._get_connection()
        try:
            self._rehydrate_from_proof(conn, account_proof)
            cur = conn.cursor()
            cur.execute("SELECT id, full_name, email FROM users WHERE email = ?", (email_norm,))
            user = cur.fetchone()
            if not user:
                raise ValueError("No account found with this registered email ID.")

            now_dt = datetime.now(timezone.utc)
            expires_dt = now_dt + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
            token = self._sign_reset_token(email_norm, int(expires_dt.timestamp()))

            cur.execute(
                "INSERT OR REPLACE INTO password_resets (token, user_id, email, expires_at, used, created_at) "
                "VALUES (?, ?, ?, ?, 0, ?)",
                (token, user["id"], email_norm, expires_dt.isoformat(), now_dt.isoformat()),
            )
            conn.commit()
            full_name = user["full_name"]
        finally:
            conn.close()

        clean_base = (base_url or "").rstrip("/")
        reset_path = f"/?reset_token={quote(token)}&email={quote(email_norm)}"
        reset_link = f"{clean_base}{reset_path}" if clean_base else reset_path
        email_sent = self._try_send_reset_email(email_norm, full_name, reset_link)

        return {
            "success": True,
            "email": email_norm,
            "token": token,
            "reset_link": reset_link,
            "expires_in_minutes": RESET_TOKEN_TTL_MINUTES,
            "email_sent": email_sent,
            "support_email": SUPPORT_EMAIL,
            "message": (
                f"Password update link sent to {email_norm}."
                if email_sent
                else f"Password update link generated for {email_norm}. Open the update link below to set your new password."
            ),
        }

    def reset_password(self, email: str, token: str, new_password: str, confirm_password: str, account_proof: Optional[str] = None) -> Dict[str, Any]:
        email_norm = normalize_email(email)
        if not EMAIL_REGEX.match(email_norm):
            raise ValueError("Please enter a valid registered email ID.")
        if not token or not token.strip():
            raise ValueError("A valid password reset link/token is required.")
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters long.")
        if new_password != confirm_password:
            raise ValueError("New password and confirmation password do not match.")

        token_clean = token.strip()
        conn = self._get_connection()
        try:
            self._rehydrate_from_proof(conn, account_proof)
            cur = conn.cursor()
            cur.execute(
                "SELECT id, full_name, email, mobile, created_at, trial_ends_at, subscription_status, subscription_plan "
                "FROM users WHERE email = ?",
                (email_norm,),
            )
            user = cur.fetchone()
            if not user:
                raise ValueError("No account found with this registered email ID.")

            cur.execute(
                "SELECT token, expires_at, used FROM password_resets WHERE token = ? AND email = ?",
                (token_clean, email_norm),
            )
            row = cur.fetchone()
            now_dt = datetime.now(timezone.utc)
            if row:
                if row["used"]:
                    raise ValueError("This password update link has already been used. Please request a new one.")
                try:
                    exp_dt = datetime.fromisoformat(row["expires_at"])
                    if exp_dt.tzinfo is None:
                        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                    if now_dt > exp_dt:
                        raise ValueError("This password update link has expired. Please request a new one.")
                except ValueError:
                    raise
                except Exception:
                    pass
            else:
                # Stateless HMAC verification fallback for serverless multi-instance safety
                if not self._verify_signed_reset_token(token_clean, email_norm):
                    raise ValueError("Invalid or expired password update link. Please request a new one.")

            pwd_hash, salt = hash_password(new_password)
            cur.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                (pwd_hash, salt, user["id"]),
            )
            cur.execute("DELETE FROM auth_sessions WHERE user_id = ?", (user["id"],))
            if row:
                cur.execute("UPDATE password_resets SET used = 1 WHERE token = ?", (token_clean,))
            conn.commit()

            new_proof = self._sign_account_proof({
                "id": user["id"],
                "full_name": user["full_name"],
                "email": email_norm,
                "mobile": user["mobile"],
                "password_hash": pwd_hash,
                "salt": salt,
                "created_at": user["created_at"],
                "trial_ends_at": user["trial_ends_at"],
                "subscription_status": user["subscription_status"],
                "subscription_plan": user["subscription_plan"],
                "updated_at": now_dt.isoformat(),
            })
        finally:
            conn.close()

        return {
            "success": True,
            "email": email_norm,
            "account_proof": new_proof,
            "message": "Password updated successfully. You can now sign in with your new password.",
        }
