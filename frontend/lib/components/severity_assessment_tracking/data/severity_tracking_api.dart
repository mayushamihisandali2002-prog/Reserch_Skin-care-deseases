import 'dart:typed_data';

import 'package:app/services/api_service.dart';

class SeverityTrackingApi {
  static Future<Map<String, dynamic>> analyzeSeverity(
    Uint8List imageBytes,
    String fileName, {
    bool track = false,
    String userId = 'anonymous',
  }) {
    return ApiService.analyzeSeverity(
      imageBytes,
      fileName,
      track: track,
      userId: userId,
    );
  }

  static Future<Map<String, dynamic>> addProgress(
    Uint8List imageBytes,
    String fileName, {
    String? journeyId,
  }) {
    return ApiService.addProgress(
      imageBytes,
      fileName,
      journeyId: journeyId,
    );
  }

  static Future<List<dynamic>> getHistory() {
    return ApiService.getHistory();
  }
}
