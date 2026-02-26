# 🗄️ Database Setup Guide - Supabase

This guide walks you through setting up Supabase for the Skin Care Assistant app.

## 📋 Table of Contents

1. [Create Supabase Account](#1-create-supabase-account)
2. [Create Database Schema](#2-create-database-schema)
3. [Configure Flutter App](#3-configure-flutter-app)
4. [Configure Python Backend](#4-configure-python-backend)
5. [Create Storage Bucket](#5-create-storage-bucket)
6. [Test the Connection](#6-test-the-connection)

---

## 1. Create Supabase Account

1. Go to **https://supabase.com** and click "Start your project"
2. Sign up with GitHub, Google, or email
3. Click **"New Project"**
4. Fill in:
   - **Name**: `skin-care-assistant`
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your users
5. Click **"Create new project"** and wait ~2 minutes

### Get Your API Keys

1. Go to **Settings → API** in your Supabase dashboard
2. Copy these values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: For Flutter app (safe to expose)
   - **service_role key**: For Python backend (keep SECRET!)

---

## 2. Create Database Schema

1. In Supabase Dashboard, go to **SQL Editor**
2. Click **"New Query"**
3. Copy the entire contents of `database/schema.sql`
4. Paste into the SQL editor
5. Click **"Run"** (or Ctrl+Enter)

You should see "Success. No rows returned" - this means the tables were created!

### Verify Tables Created

Go to **Table Editor** in the sidebar. You should see:
- ✅ profiles
- ✅ chat_sessions
- ✅ chat_messages
- ✅ skin_analyses
- ✅ diagnosis_history
- ✅ treatment_tracking

---

## 3. Configure Flutter App

### Step 1: Install Dependencies

```bash
cd app
flutter pub get
```

### Step 2: Add Your Credentials

Edit `app/lib/config/supabase_config.dart`:

```dart
class SupabaseConfig {
  // Replace with YOUR values from Supabase Dashboard → Settings → API
  static const String supabaseUrl = 'https://YOUR-PROJECT-ID.supabase.co';
  static const String supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
  
  // ... rest stays the same
}
```

### Step 3: Run the App

```bash
flutter run -d chrome
```

---

## 4. Configure Python Backend

### Step 1: Install Supabase Python Client

```bash
cd backend
pip install supabase
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### Step 2: Add Your Credentials

**Option A: Environment Variables (Recommended)**

Create a `.env` file in the `backend/` folder:

```env
SUPABASE_URL=https://YOUR-PROJECT-ID.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Option B: Direct in Code**

Edit `backend/services/supabase_service.py`:

```python
SUPABASE_URL = 'https://YOUR-PROJECT-ID.supabase.co'
SUPABASE_KEY = 'YOUR_SERVICE_ROLE_KEY'  # ⚠️ Use SERVICE key, not anon key
```

### Step 3: Test Connection

```bash
cd backend
python -c "from services import SupabaseService; print('Connected!')"
```

---

## 5. Create Storage Bucket

For storing skin images:

1. Go to **Storage** in Supabase Dashboard
2. Click **"New Bucket"**
3. Configure:
   - **Name**: `skin-images`
   - **Public**: ❌ OFF (private - requires authentication)
4. Click **"Create bucket"**

### Set Storage Policy

In the `skin-images` bucket:

1. Click **"Policies"** tab
2. Click **"New Policy"** → **"For full customization"**
3. Add policy for authenticated users:

```sql
-- Allow users to upload their own images
CREATE POLICY "Users can upload own images"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'skin-images' AND (storage.foldername(name))[1] = auth.uid()::text);

-- Allow users to view their own images
CREATE POLICY "Users can view own images"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'skin-images' AND (storage.foldername(name))[1] = auth.uid()::text);
```

---

## 6. Test the Connection

### Test Flutter Connection

In your app, after login, the Supabase service should work automatically.

### Test Python Connection

```python
from services import SupabaseService

# Initialize
SupabaseService.initialize(
    url='https://YOUR-PROJECT-ID.supabase.co',
    key='YOUR_SERVICE_ROLE_KEY'
)

# Test: Get all profiles (should return empty list initially)
client = SupabaseService.get_client()
result = client.table('profiles').select('*').execute()
print(f"Found {len(result.data)} profiles")
```

---

## 🔒 Security Notes

| Key Type | Where to Use | Exposure |
|----------|--------------|----------|
| `anon` key | Flutter app | Safe to include in app |
| `service_role` key | Python backend only | ⚠️ NEVER expose publicly |

- The `anon` key respects Row Level Security (RLS) policies
- The `service_role` key bypasses RLS - use only on server

---

## 📊 Database Schema Overview

```
┌─────────────┐       ┌─────────────────┐
│  profiles   │───────│  chat_sessions  │
│  (users)    │       │                 │
└─────────────┘       └────────┬────────┘
       │                       │
       │              ┌────────▼────────┐
       │              │  chat_messages  │
       │              └─────────────────┘
       │
       ├──────────────┬─────────────────┐
       │              │                 │
┌──────▼──────┐ ┌─────▼─────────┐ ┌─────▼──────────────┐
│skin_analyses│ │diagnosis_     │ │treatment_tracking  │
│             │ │history        │ │                    │
└─────────────┘ └───────────────┘ └────────────────────┘
```

---

## 🆘 Troubleshooting

### "Invalid API key"
- Double-check you copied the full key (they're long!)
- Make sure you're using the right key type (anon vs service_role)

### "Row Level Security policy violation"
- User might not be authenticated
- Check that the user ID matches in the RLS policy

### "relation does not exist"
- Run the `schema.sql` file in SQL Editor
- Make sure all tables were created

---

## ✅ Next Steps

After setup is complete:

1. Update the login screen to use Supabase Auth
2. Update the chat screen to persist messages
3. Update the analyze screen to save results
4. Add a history screen to view past diagnoses

Need help? Check:
- [Supabase Docs](https://supabase.com/docs)
- [Flutter Supabase Guide](https://supabase.com/docs/guides/getting-started/quickstarts/flutter)
- [Python Supabase Guide](https://supabase.com/docs/reference/python/introduction)
