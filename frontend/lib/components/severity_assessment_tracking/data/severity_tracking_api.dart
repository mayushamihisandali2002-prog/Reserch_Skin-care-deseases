import 'dart:typed_data';

import 'package:app/services/api_service.dart';

class SeverityTrackingApi {
  static Future<Map<String, dynamic>> analyzeSeverity(
    Uint8List imageBytes,
    String fileName, {
    bool track = false,
    String userId = 'anonymous',
    String? journeyId,
    String? journeyTitle,
  }) {
    return ApiService.analyzeSeverity(
      imageBytes,
      fileName,
      track: track,
      userId: userId,
      journeyId: journeyId,
      journeyTitle: journeyTitle,
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

  static Future<List<dynamic>> getHistory({String? journeyId}) {
    return ApiService.getHistory(journeyId: journeyId);
  }

  static Future<Map<String, dynamic>> getStats({String? journeyId}) {
    return ApiService.getStats(journeyId: journeyId);
  }
}
