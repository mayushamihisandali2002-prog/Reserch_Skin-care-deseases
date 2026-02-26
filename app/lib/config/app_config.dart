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
    // Production URL (when deployed)
    if (environment == Environment.production) {
      return 'https://your-production-api.com';
    }

    // Development URLs based on platform
    if (kIsWeb) {
      return 'http://127.0.0.1:5000';
    }

    if (!kIsWeb && Platform.isAndroid) {
      // Using ADB reverse port forwarding: adb reverse tcp:5000 tcp:5000
      // This makes localhost:5000 on phone connect to PC's port 5000
      return 'http://127.0.0.1:5000';
    }

    if (!kIsWeb && Platform.isIOS) {
      // For physical iOS device, use the PC's LAN IP address
      return 'http://172.28.2.98:5000';
    }

    // Windows, macOS, Linux desktop
    return 'http://127.0.0.1:5000';
  }

  /// API endpoints
  static String get healthEndpoint => '\$apiBaseUrl/api/health';
  static String get statusEndpoint => '\$apiBaseUrl/api/status';
  static String get chatEndpoint => '\$apiBaseUrl/api/chat';
  static String get analyzeEndpoint => '\$apiBaseUrl/api/analyze';
  static String get analyzeFusedEndpoint => '\$apiBaseUrl/api/analyze-fused';
  static String get historyEndpoint => '\$apiBaseUrl/api/history';
  static String get statsEndpoint => '\$apiBaseUrl/api/stats';

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
