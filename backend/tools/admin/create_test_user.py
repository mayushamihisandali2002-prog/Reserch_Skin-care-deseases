"""Create and confirm test users in Supabase Auth."""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from supabase import create_client


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_ADMIN_KEY = (
    os.getenv("SUPABASE_SECRET_KEY")
    or os.getenv("SUPABASE_SERVICE_KEY", "")
)
_db_client = None


def get_admin_headers() -> dict[str, str]:
    return {
        "apikey": SUPABASE_ADMIN_KEY,
        "Authorization": f"Bearer {SUPABASE_ADMIN_KEY}",
        "Content-Type": "application/json",
    }


def get_db_client():
    global _db_client
    if _db_client is None:
        _db_client = create_client(SUPABASE_URL, SUPABASE_ADMIN_KEY)
    return _db_client


def find_user_by_email(email: str) -> dict | None:
    headers = get_admin_headers()
    response = requests.get(f"{SUPABASE_URL}/auth/v1/admin/users", headers=headers)
    if response.status_code != 200:
        return None
    for user in response.json().get("users", []):
        if user.get("email", "").lower() == email.lower():
            return user
    return None


def ensure_profile(user_id: str, email: str, name: str) -> None:
    client = get_db_client()
    client.table("profiles").upsert(
        {
            "id": user_id,
            "email": email,
            "full_name": name,
            "tracking_preference": "weekly",
        }
    ).execute()
    print(f"  [OK] Profile ready: {email}")


def confirm_all_users() -> None:
    """Confirm all unverified users."""
    headers = get_admin_headers()

    print("\n[CHECK] Checking users...")
    response = requests.get(f"{SUPABASE_URL}/auth/v1/admin/users", headers=headers)

    if response.status_code != 200:
        print(f"[ERROR] {response.text}")
        return

    users = response.json().get("users", [])
    confirmed_count = 0

    for user in users:
        email = user.get("email", "N/A")
        is_confirmed = user.get("email_confirmed_at")
        user_id = user.get("id")

        if not is_confirmed and user_id:
            update_resp = requests.put(
                f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
                headers=headers,
                json={"email_confirm": True},
            )
            if update_resp.status_code == 200:
                print(f"  [OK] Confirmed: {email}")
                confirmed_count += 1
            else:
                print(f"  [ERROR] Failed to confirm: {email}")
        else:
            print(f"  [OK] Already confirmed: {email}")

    print(f"\n[SUMMARY] Total confirmed: {confirmed_count} users")


def create_test_user(email: str, password: str, name: str) -> bool:
    """Create a pre-confirmed test user."""
    headers = get_admin_headers()

    print(f"\n[USER] Creating user: {email}")

    response = requests.post(
        f"{SUPABASE_URL}/auth/v1/admin/users",
        headers=headers,
        json={
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"full_name": name},
        },
    )

    if response.status_code == 200:
        print("  [OK] Created and confirmed!")
        user = response.json().get("user") or response.json()
        user_id = user.get("id")
        if user_id:
            ensure_profile(user_id, email, name)
        return True

    if "already" in response.text.lower():
        print("  [INFO] User exists, confirming...")
        user = find_user_by_email(email)
        if user and user.get("id"):
            requests.put(
                f"{SUPABASE_URL}/auth/v1/admin/users/{user['id']}",
                headers=headers,
                json={"email_confirm": True},
            )
            print("  [OK] Confirmed!")
            ensure_profile(user["id"], email, name)
            return True

    print(f"  [ERROR] {response.text}")
    return False


def main() -> None:
    print("\n" + "=" * 60)
    print("  SUPABASE USER SETUP")
    print("=" * 60)

    confirm_all_users()

    test_users = [
        ("test@skincare.app", "Test123456", "Test User"),
        ("demo@skincare.app", "Demo123456", "Demo User"),
    ]

    print("\n" + "-" * 60)
    print("  CREATING TEST USERS")
    print("-" * 60)

    for email, password, name in test_users:
        create_test_user(email, password, name)

    print("\n" + "=" * 60)
    print("  LOGIN CREDENTIALS (Use any of these)")
    print("=" * 60)
    print("\n  Option 1:")
    print("    Email:    test@skincare.app")
    print("    Password: Test123456")
    print("\n  Option 2:")
    print("    Email:    demo@skincare.app")
    print("    Password: Demo123456")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
