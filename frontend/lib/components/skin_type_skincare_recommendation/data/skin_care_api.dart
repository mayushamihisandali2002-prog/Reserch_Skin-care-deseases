import 'dart:typed_data';

import 'package:app/services/api_service.dart';

class SkinCareApi {
  static Future<Map<String, dynamic>> analyze(
    Uint8List imageBytes,
    String fileName, {
    List<String> allergies = const [],
    List<String> goals = const [],
    String routineLevel = 'simple',
    String budget = 'medium',
    bool? tightAfterWash,
    bool? shinyAfter23h,
  }) {
    return ApiService.analyzeSkinCare(
      imageBytes,
      fileName,
      allergies: allergies,
      goals: goals,
      routineLevel: routineLevel,
      budget: budget,
      tightAfterWash: tightAfterWash,
      shinyAfter23h: shinyAfter23h,
    );
  }
}
