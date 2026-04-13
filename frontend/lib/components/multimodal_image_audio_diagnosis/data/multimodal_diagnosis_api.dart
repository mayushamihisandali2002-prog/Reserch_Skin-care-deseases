import 'dart:typed_data';

import 'package:app/services/api_service.dart';

class MultimodalDiagnosisApi {
  static Future<Map<String, dynamic>> analyzeImage(
    Uint8List imageBytes,
    String fileName, {
    String? journeyId,
  }) {
    return ApiService.analyzeSkin(imageBytes, fileName, journeyId: journeyId);
  }

  static Future<Map<String, dynamic>> analyzeFused(
    Uint8List imageBytes,
    String imageFileName,
    String symptoms, {
    Uint8List? audioBytes,
    String? audioFileName,
    String? journeyId,
  }) {
    return ApiService.analyzeFused(
      imageBytes,
      imageFileName,
      symptoms,
      audioBytes: audioBytes,
      audioFileName: audioFileName,
      journeyId: journeyId,
    );
  }

  static Future<Map<String, dynamic>> analyzeFusedWithAudio(
    Uint8List imageBytes,
    String imageFileName,
    Uint8List audioBytes,
    String audioFileName, {
    String? journeyId,
  }) {
    return ApiService.analyzeFusedWithAudio(
      imageBytes,
      imageFileName,
      audioBytes,
      audioFileName,
      journeyId: journeyId,
    );
  }
}
