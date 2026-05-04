// ============================================================================
// APP CONFIGURATION
// Central configuration for the Skin Care Assistant app
// ============================================================================

import 'dart:io';
import 'package:flutter/foundation.dart';

/// Environment types
enum Environment { development, staging, production }

/// App configuration singleton
class AppConfig {
  static final AppConfig _instance = AppConfig._internal();
  factory AppConfig() => _instance;
  AppConfig._internal();

  // Current environment
  static Environment environment = Environment.development;

  // ============================================================================
  // API CONFIGURATION
  // ============================================================================

  /// Get the API base URL based on platform and environment
  static String get apiBaseUrl {
    const override = String.fromEnvironment('API_BASE_URL', defaultValue: '');
    if (override.isNotEmpty) {
      return override;
    }

    // Production URL (when deployed)
    if (environment == Environment.production) {
      return 'https://your-production-api.com';
    }

    // Development URLs based on platform
    // Using 127.0.0.1 for maximum stability across Web/Desktop browsers
    if (kIsWeb) {
      return 'http://localhost:5001';
    }

    if (!kIsWeb && Platform.isAndroid) {
      // Emulator-safe default. For a physical device, pass:
      // flutter run --dart-define=API_BASE_URL=http://YOUR_PC_IP:5001
      return 'http://10.0.2.2:5001';
    }

    if (!kIsWeb && Platform.isIOS) {
      return 'http://127.0.0.1:5001';
    }

    // Windows, macOS, Linux desktop
    return 'http://localhost:5001';
  }

  /// API endpoints
  static String get healthEndpoint => '$apiBaseUrl/api/health';
  static String get statusEndpoint => '$apiBaseUrl/api/status';
  static String get chatEndpoint => '$apiBaseUrl/api/chat';
  // Deprecated compatibility endpoint. New diagnosis flows must use analyzeFusedEndpoint.
  static String get analyzeEndpoint => '$apiBaseUrl/api/analyze';
  static String get analyzeFusedEndpoint => '$apiBaseUrl/api/analyze-fused';
  static String get historyEndpoint => '$apiBaseUrl/api/history';
  static String get statsEndpoint => '$apiBaseUrl/api/stats';

  // ============================================================================
  // APP SETTINGS
  // ============================================================================

  static const String appName = 'Skin Care Assistant';
  static const String appVersion = '1.0.0';

  // Request timeouts
  static const Duration apiTimeout = Duration(seconds: 30);
  static const Duration imageUploadTimeout = Duration(seconds: 60);

  // ============================================================================
  // FEATURE FLAGS
  // ============================================================================

  static bool get enableDebugMode => environment == Environment.development;
  static bool get enableAnalytics => environment == Environment.production;
  static bool get enableCrashReporting => environment == Environment.production;

  // ============================================================================
  // DISEASE CLASSES (matches backend model)
  // ============================================================================

  static const List<String> diseaseClasses = [
    'Eczema',
    'Dermatitis',
    'Psoriasis',
    'Acne',
    'Urticaria',
    'Pigmentation / Dark Spots',
    'Ringworm',
    'Rosacea',
    'Shingles',
    'Vitiligo',
    'Impetigo',
    'Molluscum Contagiosum',
    'Folliculitis',
    'Scabies',
    'Warts',
    'Seborrheic Dermatitis',
    'Lichen Planus',
    'Cellulitis',
    'Herpes Simplex',
    'Pityriasis Versicolor',
    'Melanoma',
    'Basal Cell Carcinoma',
    'Actinic Keratosis',
    'Seborrheic Keratosis',
    'Dermatofibroma',
    'Cherry Angioma',
    'Melanocytic Nevi',
    'Hidradenitis Suppurativa',
    'Alopecia Areata',
    'Melasma',
  ];

  /// Get color for confidence level
  static int getConfidenceColor(String level) {
    switch (level.toLowerCase()) {
      case 'high':
        return 0xFF4CAF50; // Green
      case 'medium':
        return 0xFFFF9800; // Orange
      case 'low':
        return 0xFFF44336; // Red
      default:
        return 0xFF9E9E9E; // Grey
    }
  }
}
