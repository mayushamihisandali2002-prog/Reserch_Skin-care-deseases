# Authentication Setup Guide

This guide will help you set up authentication for the Skin Care Assistant app, including email/password and Google Sign-In.

## Prerequisites

- A [Supabase](https://supabase.com) account and project
- A [Google Cloud Console](https://console.cloud.google.com) account
- Flutter SDK installed

---

## Step 1: Supabase Configuration

### 1.1 Get Supabase Credentials

1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to **Settings** → **API**
4. Copy the following values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)

5. Update `lib/config/supabase_config.dart`:
   ```dart
   static const String supabaseUrl = 'YOUR_SUPABASE_URL';
   static const String supabaseAnonKey = 'YOUR_ANON_KEY';
   ```

### 1.2 Create Database Tables (Optional)

If you want to store user profiles, run this SQL in Supabase SQL Editor:

```sql
-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  full_name TEXT,
  skin_type TEXT,
  gender TEXT,
  date_of_birth DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS (Row Level Security)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Create policy for users to see their own profile
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

-- Create policy for users to update their own profile
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- Create policy for users to insert their own profile
CREATE POLICY "Users can insert own profile" ON profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

-- Trigger to create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name)
  VALUES (new.id, new.raw_user_meta_data->>'full_name');
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

---

## Step 2: Google OAuth Setup

### 2.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** → **OAuth consent screen**
4. Configure the consent screen:
   - User Type: **External**
   - App name: `Skin Care Assistant`
   - User support email: Your email
   - Add scopes: `email`, `profile`
   - Save

### 2.2 Create OAuth 2.0 Credentials

Navigate to **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**

#### For Web Application:
1. Application type: **Web application**
2. Name: `Skin Care Assistant Web`
3. Authorized JavaScript origins:
   - `http://localhost:3000` (for development)
   - `http://localhost:5000` (for development)
   - Your production domain
4. Authorized redirect URIs:
   - `https://YOUR_SUPABASE_URL/auth/v1/callback`
5. Create and copy the **Client ID** and **Client Secret**

#### For Android:
1. Application type: **Android**
2. Name: `Skin Care Assistant Android`
3. Package name: `com.example.app` (check your `android/app/build.gradle.kts`)
4. SHA-1 certificate fingerprint:
   ```bash
   # For debug certificate (Windows):
   keytool -list -v -keystore %USERPROFILE%\.android\debug.keystore -alias androiddebugkey -storepass android -keypass android
   
   # For debug certificate (Mac/Linux):
   keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android
   ```
5. Create and copy the **Client ID**

#### For iOS:
1. Application type: **iOS**
2. Name: `Skin Care Assistant iOS`
3. Bundle ID: `com.example.app` (check your `ios/Runner/Info.plist`)
4. Create and copy the **Client ID**

### 2.3 Update Flutter Configuration

Update `lib/config/supabase_config.dart`:
```dart
static const String googleWebClientId = 'YOUR_WEB_CLIENT_ID.apps.googleusercontent.com';
static const String googleAndroidClientId = 'YOUR_ANDROID_CLIENT_ID.apps.googleusercontent.com';
static const String googleIosClientId = 'YOUR_IOS_CLIENT_ID.apps.googleusercontent.com';
```

### 2.4 Configure Supabase Google Provider

1. Go to your Supabase Dashboard
2. Navigate to **Authentication** → **Providers**
3. Enable **Google**
4. Enter:
   - **Client ID**: Your Web Client ID
   - **Client Secret**: Your Web Client Secret
5. Save

---

## Step 3: Platform-Specific Configuration

### 3.1 Android Configuration

1. Update `android/app/build.gradle.kts`:
   ```kotlin
   android {
       defaultConfig {
           applicationId = "com.yourcompany.skincare"
           // ... other config
       }
   }
   ```

2. Add to `android/app/src/main/AndroidManifest.xml` inside `<application>`:
   ```xml
   <meta-data
       android:name="com.google.android.gms.ads.APPLICATION_ID"
       android:value="YOUR_ANDROID_CLIENT_ID"/>
   ```

### 3.2 iOS Configuration

1. Open `ios/Runner/Info.plist` and add:
   ```xml
   <key>CFBundleURLTypes</key>
   <array>
       <dict>
           <key>CFBundleURLSchemes</key>
           <array>
               <string>com.googleusercontent.apps.YOUR_IOS_CLIENT_ID</string>
           </array>
       </dict>
   </array>
   ```

2. Update Bundle Identifier in Xcode to match your iOS Client ID configuration

### 3.3 Web Configuration

For web, ensure your `web/index.html` includes:
```html
<meta name="google-signin-client_id" content="YOUR_WEB_CLIENT_ID.apps.googleusercontent.com">
```

---

## Step 4: Test Authentication

### Run the app:
```bash
cd app
flutter pub get
flutter run
```

### Test scenarios:
1. **Email/Password Registration**: Create a new account
2. **Email/Password Login**: Sign in with existing account
3. **Google Sign-In**: Use Google account to sign in
4. **Password Reset**: Request password reset email
5. **Logout**: Sign out from the app

---

## Troubleshooting

### Common Issues:

#### "Google Sign-In was cancelled"
- User cancelled the popup
- No action needed

#### "No Access Token found"
- Google OAuth not configured correctly
- Check client IDs and secrets

#### "Invalid email or password"
- Check credentials
- Ensure email is verified (if confirmation required)

#### Google Sign-In not working on Android
- Verify SHA-1 fingerprint is correct
- Check package name matches

#### Google Sign-In not working on iOS
- Verify Bundle ID matches
- Check URL scheme is configured

### Debug Mode

To enable verbose logging, add to your app:
```dart
// In main.dart
import 'package:flutter/foundation.dart';

void main() {
  if (kDebugMode) {
    debugPrint('Supabase URL: ${SupabaseConfig.supabaseUrl}');
  }
  // ... rest of main
}
```

---

## Security Notes

1. **Never commit secrets**: Add `supabase_config.dart` to `.gitignore` if it contains sensitive data
2. **Use environment variables**: For production, use flutter_dotenv or similar
3. **Enable RLS**: Always enable Row Level Security on Supabase tables
4. **HTTPS only**: Use HTTPS for all production URLs

---

## Support

- [Supabase Documentation](https://supabase.com/docs)
- [Google Sign-In for Flutter](https://pub.dev/packages/google_sign_in)
- [Flutter Authentication Codelab](https://docs.flutter.dev/cookbook/persistence/authenticate)
