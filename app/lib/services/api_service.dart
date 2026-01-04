import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiService {
  // Use 10.0.2.2 for Android Emulator
  // Use 172.28.1.12 (Your PC IP) for Physical Device
  static String get baseUrl {
    if (kIsWeb) return 'http://localhost:5000';
    if (Platform.isAndroid) {
       // CHANGE THIS to your PC's IP address if running on a real phone
       // Run 'ipconfig' in terminal to find your IPv4 address
       return 'http://172.28.1.12:5000'; 
       // return 'http://10.0.2.2:5000'; // Keep this for Emulator
    }
    return 'http://localhost:5000';
  }

  static Future<Map<String, dynamic>> analyzeSkin(String imagePath) async {
    try {
      // For a real app, we'd upload the file. 
      // Here we just hit the endpoint to get dummy data.
      final response = await http.post(Uri.parse('$baseUrl/api/analyze'));
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to analyze skin');
      }
    } catch (e) {
      print("Error analyzing skin: $e");
      rethrow;
    }
  }

  static Future<Map<String, dynamic>> analyzeSkinCare(String imagePath) async {
    try {
      final response = await http.post(Uri.parse('$baseUrl/api/analyze-skin-care'));
      
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

  static Future<String> sendChatMessage(String message) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/chat'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'message': message}),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['response'];
      } else {
        throw Exception('Failed to send message');
      }
    } catch (e) {
      print("Error chatting: $e");
      return "Error: Could not connect to assistant.";
    }
  }
}
