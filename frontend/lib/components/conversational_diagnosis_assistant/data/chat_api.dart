import 'package:app/services/api_service.dart';

class ChatApi {
  static Future<Map<String, dynamic>> sendMessage(String message) {
    return ApiService.sendChatMessage(message);
  }
}
