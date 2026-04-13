"""Create and confirm test users in Supabase Auth"""
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment variables
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

# Supabase config - load from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
SUPABASE_ADMIN_KEY = os.getenv('SUPABASE_SECRET_KEY') or os.getenv('SUPABASE_SERVICE_KEY', '')

def get_admin_headers():
    return {
        'apikey': SUPABASE_ADMIN_KEY,
        'Authorization': f'Bearer {SUPABASE_ADMIN_KEY}',
        'Content-Type': 'application/json'
    }

def confirm_all_users():
    """Confirm all unverified users"""
    headers = get_admin_headers()
    
    print("\n🔍 Checking users...")
    response = requests.get(
        f'{SUPABASE_URL}/auth/v1/admin/users',
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return
    
    users = response.json().get('users', [])
    confirmed_count = 0
    
    for user in users:
        email = user.get('email', 'N/A')
        is_confirmed = user.get('email_confirmed_at')
        user_id = user.get('id')
        
        if not is_confirmed and user_id:
            update_resp = requests.put(
                f'{SUPABASE_URL}/auth/v1/admin/users/{user_id}',
                headers=headers,
                json={'email_confirm': True}
            )
            if update_resp.status_code == 200:
                print(f"  ✅ Confirmed: {email}")
                confirmed_count += 1
            else:
                print(f"  ❌ Failed to confirm: {email}")
        else:
            print(f"  ✓ Already confirmed: {email}")
    
    print(f"\n📊 Total confirmed: {confirmed_count} users")

def create_test_user(email, password, name):
    """Create a pre-confirmed test user"""
    headers = get_admin_headers()
    
    print(f"\n👤 Creating user: {email}")
    
    response = requests.post(
        f'{SUPABASE_URL}/auth/v1/admin/users',
        headers=headers,
        json={
            'email': email,
            'password': password,
            'email_confirm': True,
            'user_metadata': {
                'full_name': name
            }
        }
    )
    
    if response.status_code == 200:
        print(f"  ✅ Created and confirmed!")
        return True
    elif 'already' in response.text.lower():
        print(f"  ℹ️ User exists, confirming...")
        # Find and confirm
        users_resp = requests.get(f'{SUPABASE_URL}/auth/v1/admin/users', headers=headers)
        for user in users_resp.json().get('users', []):
            if user.get('email') == email:
                requests.put(
                    f'{SUPABASE_URL}/auth/v1/admin/users/{user["id"]}',
                    headers=headers,
                    json={'email_confirm': True}
                )
                print(f"  ✅ Confirmed!")
                return True
    else:
        print(f"  ❌ Error: {response.text}")
    return False

def main():
    print("\n" + "="*60)
    print("  SUPABASE USER SETUP")
    print("="*60)
    
    # Confirm all existing users
    confirm_all_users()
    
    # Create test users
    test_users = [
        ('test@skincare.app', 'Test123456', 'Test User'),
        ('demo@skincare.app', 'Demo123456', 'Demo User'),
    ]
    
    print("\n" + "-"*60)
    print("  CREATING TEST USERS")
    print("-"*60)
    
    for email, password, name in test_users:
        create_test_user(email, password, name)
    
    # Print credentials
    print("\n" + "="*60)
    print("  ✅ LOGIN CREDENTIALS (Use any of these)")
    print("="*60)
    print("\n  Option 1:")
    print("    📧 Email:    test@skincare.app")
    print("    🔑 Password: Test123456")
    print("\n  Option 2:")
    print("    📧 Email:    demo@skincare.app")
    print("    🔑 Password: Demo123456")
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()
