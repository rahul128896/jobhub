"""
otp_utils.py
============
OTP generation, storage, and verification for 2-step registration and optional 2FA.

All SQL uses %s placeholders (required by PyMySQL / MySQL).

Features:
  - 6-digit random numeric OTP
  - 5-minute expiry (set OTP_EXPIRY_MINUTES in .env)
  - Max 3 wrong attempts before OTP is locked (LOCK_AFTER_ATTEMPTS)
  - OTP deleted after successful use (one-time use only)
"""

import os
import random
import string
import datetime
from database import get_db

# ── Config ─────────────────────────────────────────────────────────────
OTP_EXPIRY_MINUTES  = int(os.environ.get('OTP_EXPIRY_MINUTES', 5))
OTP_LENGTH          = 6
LOCK_AFTER_ATTEMPTS = 3   # Lock OTP after this many wrong guesses


# ── Generate OTP ───────────────────────────────────────────────────────
def generate_otp(length: int = OTP_LENGTH) -> str:
    """Return a random 6-digit numeric string e.g. '483920'"""
    return ''.join(random.choices(string.digits, k=length))


# ── Store OTP ──────────────────────────────────────────────────────────
def store_otp(user_id: int, email: str, otp: str) -> bool:
    """
    Save a new OTP to the database.
    - Deletes any previous OTP for this user (only one active at a time).
    - Sets expiry timestamp.
    - Resets attempt counter to 0.
    """
    try:
        conn = get_db()

        expiry = (
            datetime.datetime.utcnow()
            + datetime.timedelta(minutes=OTP_EXPIRY_MINUTES)
        ).strftime('%Y-%m-%d %H:%M:%S')

        # Remove any old OTP for this user
        conn.execute('DELETE FROM otp_attempts WHERE user_id = %s', (user_id,))

        # Insert fresh OTP
        conn.execute("""
            INSERT INTO otp_attempts (user_id, email, otp, expires_at, attempt_count)
            VALUES (%s, %s, %s, %s, 0)
        """, (user_id, email, otp, expiry))

        conn.commit()
        conn.close()
        print(f"[OTP] Stored OTP for user_id={user_id}, expires={expiry}")
        return True

    except Exception as e:
        print(f"[OTP] Error storing OTP: {e}")
        return False


# ── Verify OTP ─────────────────────────────────────────────────────────
def verify_otp(user_id: int, otp: str) -> dict:
    """
    Verify the OTP entered by the user.

    Returns:
        {'valid': True, 'message': '...'}   on success
        {'valid': False, 'message': '...'}  on failure (expired / wrong / locked)
    """
    try:
        conn = get_db()

        # Fetch latest OTP record for this user
        conn.execute("""
            SELECT * FROM otp_attempts
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        row = conn.fetchone()

        if not row:
            conn.close()
            return {'valid': False, 'message': 'No OTP found. Please request a new one.'}

        # ── Check attempt limit ─────────────────────────────────────────
        attempt_count = row.get('attempt_count', 0)
        if attempt_count >= LOCK_AFTER_ATTEMPTS:
            conn.close()
            return {
                'valid':   False,
                'message': f'Too many wrong attempts ({LOCK_AFTER_ATTEMPTS} max). '
                           'Please request a new OTP.'
            }

        # ── Check expiry ────────────────────────────────────────────────
        expires_at = row['expires_at']
        # expires_at may be a datetime object (PyMySQL) or a string
        if isinstance(expires_at, str):
            expires_at = datetime.datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.utcnow() > expires_at:
            conn.close()
            return {'valid': False, 'message': 'OTP has expired. Please request a new one.'}

        # ── Check OTP value ─────────────────────────────────────────────
        if row['otp'] != otp:
            # Increment attempt counter
            conn.execute("""
                UPDATE otp_attempts
                SET attempt_count = attempt_count + 1
                WHERE user_id = %s
            """, (user_id,))
            conn.commit()

            remaining = LOCK_AFTER_ATTEMPTS - (attempt_count + 1)
            conn.close()

            if remaining <= 0:
                return {
                    'valid':   False,
                    'message': 'Incorrect OTP. No attempts remaining. Please request a new OTP.'
                }
            return {
                'valid':   False,
                'message': f'Incorrect OTP. {remaining} attempt(s) remaining.'
            }

        # ── OTP matches ─────────────────────────────────────────────────
        conn.close()
        return {'valid': True, 'message': 'OTP verified successfully'}

    except Exception as e:
        print(f"[OTP] Error verifying OTP: {e}")
        return {'valid': False, 'message': 'Error verifying OTP. Please try again.'}


# ── Mark OTP Used ──────────────────────────────────────────────────────
def mark_otp_used(user_id: int, otp: str) -> bool:
    """Delete the OTP after successful login so it cannot be reused."""
    try:
        conn = get_db()
        conn.execute(
            'DELETE FROM otp_attempts WHERE user_id = %s AND otp = %s',
            (user_id, otp)
        )
        conn.commit()
        conn.close()
        print(f"[OTP] OTP used and deleted for user_id={user_id}")
        return True
    except Exception as e:
        print(f"[OTP] Error deleting used OTP: {e}")
        return False


# ── Cleanup Expired OTPs ───────────────────────────────────────────────
def cleanup_expired_otps() -> bool:
    """Remove all expired OTPs from the database (call periodically)."""
    try:
        conn = get_db()
        conn.execute("DELETE FROM otp_attempts WHERE expires_at < NOW()")
        conn.commit()
        conn.close()
        print(f"[OTP] Cleaned up expired OTP(s)")
        return True
    except Exception as e:
        print(f"[OTP] Error cleaning expired OTPs: {e}")
        return False

