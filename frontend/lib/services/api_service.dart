import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';
import '../config/app_config.dart';
import 'supabase_service.dart';

class ApiService {
  // Session ID for tracking conversations across the app lifetime
  static final String sessionId = const Uuid().v4();

  // Use centralized config for API URL
  static String get baseUrl => AppConfig.apiBaseUrl;

  /// Analyze skin image only (image-based diagnosis)
  static Future<Map<String, dynamic>> analyzeSkin(
    Uint8List imageBytes,
    String fileName, {
    String? journeyId,
  }) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/analyze'),
      );

      request.files.add(
        http.MultipartFile.fromBytes('image', imageBytes, filename: fileName),
      );

      if (journeyId != null) request.fields['journey_id'] = journeyId;
      if (SupabaseService.userId != null) {
        request.fields['user_id'] = SupabaseService.userId!;
      }

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to analyze skin: ${response.body}');
      }
    } catch (e) {
      debugPrint("Error analyzing skin: $e");
      rethrow;
    }
  }

  /// Analyze skin with both image and text symptoms (fused multimodal diagnosis)
  /// Optionally includes audio voice note for speech-to-text processing
  /// Works on both web and mobile/desktop platforms
  static Future<Map<String, dynamic>> analyzeFused(
    Uint8List imageBytes,
    String imageFileName,
    String symptoms, {
    Uint8List? audioBytes,
    String? audioFileName,
    String? journeyId,
  }) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/analyze-fused'),
      );

      // Add the image file using bytes (works on all platforms)
      request.files.add(
        http.MultipartFile.fromBytes(
          'image',
          imageBytes,
          filename: imageFileName,
        ),
      );

      // Add the symptom text
      request.fields['text'] = symptoms;
      if (journeyId != null) request.fields['journey_id'] = journeyId;
      if (SupabaseService.userId != null) {
        request.fields['user_id'] = SupabaseService.userId!;
      }

      // Add audio file if provided
      if (audioBytes != null && audioFileName != null) {
        request.files.add(
          http.MultipartFile.fromBytes(
            'audio',
            audioBytes,
            filename: audioFileName,
          ),
        );
      }

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to analyze: ${response.body}');
      }
    } catch (e) {
      debugPrint("Error in fused analysis: $e");
      rethrow;
    }
  }

  /// Analyze skin with image and audio file (audio will be transcribed on server)
  static Future<Map<String, dynamic>> analyzeFusedWithAudio(
    Uint8List imageBytes,
    String imageFileName,
    Uint8List audioBytes,
    String audioFileName, {
    String? journeyId,
  }) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/analyze-fused'),
      );

      request.files.add(
        http.MultipartFile.fromBytes(
          'image',
          imageBytes,
          filename: imageFileName,
        ),
      );

      request.files.add(
        http.MultipartFile.fromBytes(
          'audio',
          audioBytes,
          filename: audioFileName,
        ),
      );

      request.fields['text'] = '';
      if (journeyId != null) request.fields['journey_id'] = journeyId;
      if (SupabaseService.userId != null) {
        request.fields['user_id'] = SupabaseService.userId!;
      }

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);
      if (response.statusCode == 200) return json.decode(response.body);
      throw Exception('Failed to analyze: ${response.body}');
    } catch (e) {
      debugPrint("Error in fused analysis with audio: $e");
      rethrow;
    }
  }

  /// FULLY AUTOMATED SMART SCAN
  static Future<Map<String, dynamic>> smartScan({
    Uint8List? imageBytes,
    String? imageFileName,
    String? message,
    String? journeyId,
  }) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/smart-scan'),
      );

      if (imageBytes != null && imageFileName != null) {
        request.files.add(
          http.MultipartFile.fromBytes(
            'image',
            imageBytes,
            filename: imageFileName,
          ),
        );
      }

      if (message != null) request.fields['message'] = message;
      if (journeyId != null) request.fields['journey_id'] = journeyId;
      if (SupabaseService.userId != null) {
        request.fields['user_id'] = SupabaseService.userId!;
      }

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);
      if (response.statusCode == 200) return json.decode(response.body);
      throw Exception('Smart scan failed: ${response.body}');
    } catch (e) {
      debugPrint("Error in smart scan: $e");
      rethrow;
    }
  }

  static Future<Map<String, dynamic>> analyzeSkinCare(
    Uint8List imageBytes,
    String fileName, {
    List<String> allergies = const [],
    List<String> goals = const [],
    String routineLevel = 'simple',
    String budget = 'medium',
    bool? tightAfterWash,
    bool? shinyAfter23h,
  }) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/analyze-skin-care'),
      );

      request.files.add(
        http.MultipartFile.fromBytes('image', imageBytes, filename: fileName),
      );

      if (allergies.isNotEmpty) {
        request.fields['allergies'] = allergies.join(',');
      }
      if (goals.isNotEmpty) {
        request.fields['goals'] = goals.join(',');
      }
      request.fields['routine_level'] = routineLevel;
      request.fields['budget'] = budget;
      if (tightAfterWash != null) {
        request.fields['tight_after_wash'] = tightAfterWash ? 'yes' : 'no';
      }
      if (shinyAfter23h != null) {
        request.fields['shiny_after_2_3h'] = shinyAfter23h ? 'yes' : 'no';
      }

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to analyze skin care: ${response.body}');
      }
    } catch (e) {
      debugPrint("Error analyzing skin care: $e");
      rethrow;
    }
  }

  static Future<Map<String, dynamic>> analyzeSeverity(
    Uint8List imageBytes,
    String fileName, {
    bool track = false,
    String userId = 'anonymous',
  }) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/analyze-severity'),
      );

      request.files.add(
        http.MultipartFile.fromBytes('image', imageBytes, filename: fileName),
      );
      request.fields['track'] = track ? 'true' : 'false';
      request.fields['user_id'] = userId;

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to analyze severity: ${response.body}');
      }
    } catch (e) {
      debugPrint("Error analyzing severity: $e");
      rethrow;
    }
  }

  static Future<Map<String, dynamic>> addProgress(
    Uint8List imageBytes,
    String fileName, {
    String? journeyId,
  }) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/progress'),
      );

      request.files.add(
        http.MultipartFile.fromBytes('image', imageBytes, filename: fileName),
      );

      if (journeyId != null) request.fields['journey_id'] = journeyId;
      if (SupabaseService.userId != null) {
        request.fields['user_id'] = SupabaseService.userId!;
      }

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to log progress: ${response.body}');
      }
    } catch (e) {
      debugPrint("Error logging progress: $e");
      rethrow;
    }
  }

  static Future<List<dynamic>> getHistory({String? userId}) async {
    try {
      final uid = userId ?? SupabaseService.userId;
      if (uid == null || uid.trim().isEmpty || uid == 'anonymous') {
        return [];
      }
      final response = await http.get(Uri.parse('$baseUrl/api/history?user_id=$uid'));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load history');
      }
    } catch (e) {
      debugPrint("Error getting history: $e");
      return [];
    }
  }

  static Future<Map<String, dynamic>> getStats({String? userId}) async {
    try {
      final uid = userId ?? SupabaseService.userId;
      if (uid == null || uid.trim().isEmpty || uid == 'anonymous') {
        return {
          'labels': ['Redness', 'Inflammation', 'Scaling', 'Texture'],
          'values': [0, 0, 0, 0],
          'note': 'Login is required to view tracking statistics.',
        };
      }
      final response = await http.get(Uri.parse('$baseUrl/api/stats?user_id=$uid'));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load stats');
      }
    } catch (e) {
      debugPrint("Error getting stats: $e");
      return {
        'labels': ['Redness', 'Inflammation', 'Scaling', 'Texture'],
        'values': [0, 0, 0, 0],
        'note': 'Tracking statistics are currently unavailable.',
      };
    }
  }

  static Future<Map<String, dynamic>> getSystemStatus() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/status'));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load system status');
      }
    } catch (e) {
      debugPrint("Error getting system status: $e");
      return {};
    }
  }

  static Future<Map<String, dynamic>> sendChatMessage(String message) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/chat'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'message': message,
          'session_id':
              sessionId, // Include session ID for conversation tracking
        }),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data;
      } else {
        throw Exception('Failed to send message');
      }
    } catch (e) {
      debugPrint("Error chatting: $e");
      return {
        "reply": "Error: Could not connect to assistant.",
        "predicted_disease": null,
        "confidence": 0.0,
        "confidence_level": "none",
        "needs_more_info": true,
        "follow_up_questions": [],
        "recommended_treatments": [],
        "model_status": "offline",
        "error": e.toString(),
      };
    }
  }
}
