// ============================================================================
// SUPABASE CONFIGURATION
// Add your Supabase credentials here
// ============================================================================

class SupabaseConfig {
  // Supabase project credentials
  // From: Supabase Dashboard > Settings > API

  static const String supabaseUrl = 'https://bsgvtoaadjulgccwqrdj.supabase.co';
  static const String supabaseAnonKey =
      'sb_publishable_WcVdg4dwPA_XPim3oSQ2bQ_EgS1O69P';

  // ============================================================================
  // GOOGLE OAUTH CONFIGURATION
  // Setup Instructions:
  // 1. Go to Google Cloud Console: https://console.cloud.google.com/
  // 2. Create a new project or select existing one
  // 3. Enable "Google Sign-In API"
  // 4. Go to "APIs & Services" > "Credentials"
  // 5. Create OAuth 2.0 Client IDs for each platform:
  //
  // FOR WEB:
  //   - Application type: Web application
  //   - Authorized JavaScript origins: http://localhost:3000 (for dev)
  //   - Authorized redirect URIs: YOUR_SUPABASE_URL/auth/v1/callback
  //
  // FOR ANDROID:
  //   - Application type: Android
  //   - Package name: com.example.app (from AndroidManifest.xml)
  //   - SHA-1 certificate: Run `keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android`
  //
  // FOR iOS:
  //   - Application type: iOS
  //   - Bundle ID: com.example.app (from Info.plist)
  //
  // 6. Copy the Client IDs below:
  // ============================================================================

  // TODO: Replace these with your actual Google OAuth Client IDs
  static const String googleWebClientId =
      'YOUR_WEB_CLIENT_ID.apps.googleusercontent.com';
  static const String googleAndroidClientId =
      'YOUR_ANDROID_CLIENT_ID.apps.googleusercontent.com';
  static const String googleIosClientId =
      'YOUR_IOS_CLIENT_ID.apps.googleusercontent.com';

  // ============================================================================
  // SUPABASE GOOGLE PROVIDER SETUP:
  // 1. Go to Supabase Dashboard > Authentication > Providers
  // 2. Enable Google provider
  // 3. Add your Google Web Client ID and Client Secret
  // 4. Save the configuration
  // ============================================================================

  // Storage bucket names
  static const String skinImagesBucket = 'skin-images';

  // Table names
  static const String profilesTable = 'profiles';
  static const String chatSessionsTable = 'chat_sessions';
  static const String chatMessagesTable = 'chat_messages';
  static const String skinAnalysesTable = 'skin_analyses';
  static const String diagnosisHistoryTable = 'diagnosis_history';
  static const String treatmentTrackingTable = 'treatment_tracking';
}
