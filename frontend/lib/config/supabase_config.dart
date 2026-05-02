// ============================================================================
// SUPABASE CONFIGURATION
// Supabase and OAuth settings are injected at build time via --dart-define.
// ============================================================================

class SupabaseConfig {
  // Supabase project credentials
  // Pass these when running/building Flutter:
  //   --dart-define=SUPABASE_URL=https://YOUR_PROJECT.supabase.co
  //   --dart-define=SUPABASE_ANON_KEY=YOUR_PUBLISHABLE_OR_ANON_KEY
  // or:
  //   --dart-define=SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_KEY
  static const String supabaseUrl =
      String.fromEnvironment(
        'SUPABASE_URL',
        defaultValue: 'https://bsgvtoaadjulgccwqrdj.supabase.co',
      );
  static const String _supabaseAnonKey =
      String.fromEnvironment(
        'SUPABASE_ANON_KEY',
        defaultValue: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJzZ3Z0b2FhZGp1bGdjY3dxcmRqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwMDA0ODIsImV4cCI6MjA4NzU3NjQ4Mn0.pYnMgJFnIlB1Ev0ge8PQIN7VA2u7lpRiUkXwawavNX8',
      );
  static const String _supabasePublishableKey =
      String.fromEnvironment(
        'SUPABASE_PUBLISHABLE_KEY',
        defaultValue: 'sb_publishable_WcVdg4dwPA_XPim3oSQ2bQ_EgS1O69P',
      );

  static String get supabaseAnonKey {
    final anon = _supabaseAnonKey.trim();
    if (anon.isNotEmpty) {
      return anon;
    }
    return _supabasePublishableKey.trim();
  }

  // Google OAuth client IDs
  static const String googleWebClientId =
      String.fromEnvironment('GOOGLE_WEB_CLIENT_ID', defaultValue: '');
  static const String googleAndroidClientId =
      String.fromEnvironment('GOOGLE_ANDROID_CLIENT_ID', defaultValue: '');
  static const String googleIosClientId =
      String.fromEnvironment('GOOGLE_IOS_CLIENT_ID', defaultValue: '');

  static bool get isSupabaseConfigured {
    final hasUrl = supabaseUrl.trim().isNotEmpty;
    final hasKey = supabaseAnonKey.trim().isNotEmpty;
    return hasUrl && hasKey;
  }

  static String get configurationError {
    return 'Supabase is not configured for this build. Run Flutter with '
        '--dart-define=SUPABASE_URL=... and '
        '--dart-define=SUPABASE_ANON_KEY=... '
        'or --dart-define=SUPABASE_PUBLISHABLE_KEY=...';
  }

  static bool get isGoogleAuthConfigured {
    return googleWebClientId.trim().isNotEmpty ||
        googleAndroidClientId.trim().isNotEmpty ||
        googleIosClientId.trim().isNotEmpty;
  }

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
