import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';
import '../config/app_config.dart';

class ApiService {
  // Session ID for tracking conversations across the app lifetime
  static final String sessionId = const Uuid().v4();

  // Use centralized config for API URL
  static String get baseUrl => AppConfig.apiBaseUrl;

  /// Analyze skin image only (image-based diagnosis)
  static Future<Map<String, dynamic>> analyzeSkin(String imagePath) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/analyze'),
      );

      // Add the image file
      request.files.add(await http.MultipartFile.fromPath('image', imagePath));

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to analyze skin: ${response.body}');
      }
    } catch (e) {
      print("Error analyzing skin: $e");
      rethrow;
    }
  }

  /// Analyze skin with both image and text symptoms (fused multimodal diagnosis)
  static Future<Map<String, dynamic>> analyzeFused(
    String imagePath,
    String symptoms,
  ) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/analyze-fused'),
      );

      // Add the image file
      request.files.add(await http.MultipartFile.fromPath('image', imagePath));

      // Add the symptom text
      request.fields['text'] = symptoms;

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to analyze: ${response.body}');
      }
    } catch (e) {
      print("Error in fused analysis: $e");
      rethrow;
    }
  }

  static Future<Map<String, dynamic>> analyzeSkinCare(String imagePath) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/analyze-skin-care'),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to analyze skin care');
      }
    } catch (e) {
      print("Error analyzing skin care: $e");
      rethrow;
    }
  }

  static Future<Map<String, dynamic>> addProgress(String imagePath) async {
    try {
      final response = await http.post(Uri.parse('$baseUrl/api/progress'));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to log progress');
      }
    } catch (e) {
      print("Error logging progress: $e");
      rethrow;
    }
  }

  static Future<List<dynamic>> getHistory() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/history'));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load history');
      }
    } catch (e) {
      print("Error getting history: $e");
      return [];
    }
  }

  static Future<Map<String, dynamic>> getStats() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/stats'));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load stats');
      }
    } catch (e) {
      print("Error getting stats: $e");
      return {'labels': [], 'values': []};
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
      print("Error chatting: $e");
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
