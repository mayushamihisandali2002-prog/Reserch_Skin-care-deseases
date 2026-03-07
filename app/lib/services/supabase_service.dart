import 'dart:io';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:google_sign_in/google_sign_in.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../config/supabase_config.dart';

/// Supabase service for database operations
class SupabaseService {
  static SupabaseClient get client => Supabase.instance.client;
  static User? get currentUser => client.auth.currentUser;
  static String? get userId => currentUser?.id;

  // ============================================================================
  // INITIALIZATION
  // ============================================================================

  static Future<void> initialize() async {
    await Supabase.initialize(
      url: SupabaseConfig.supabaseUrl,
      anonKey: SupabaseConfig.supabaseAnonKey,
    );
  }

  // ============================================================================
  // AUTHENTICATION
  // ============================================================================

  /// Sign up with email and password
  static Future<AuthResponse> signUp({
    required String email,
    required String password,
    String? fullName,
  }) async {
    final response = await client.auth.signUp(
      email: email,
      password: password,
      data: {'full_name': fullName},
    );
    return response;
  }

  /// Sign in with email and password
  static Future<AuthResponse> signIn({
    required String email,
    required String password,
  }) async {
    return await client.auth.signInWithPassword(
      email: email,
      password: password,
    );
  }

  /// Sign out
  static Future<void> signOut() async {
    await client.auth.signOut();
  }

  /// Sign in with Google
  /// Requires Google OAuth to be configured in Supabase Dashboard:
  /// Authentication > Providers > Google
  static Future<AuthResponse> signInWithGoogle() async {
    final GoogleSignIn googleSignIn = GoogleSignIn(
      clientId: kIsWeb ? SupabaseConfig.googleWebClientId : null,
      serverClientId: SupabaseConfig.googleWebClientId,
      scopes: ['email', 'profile'],
    );

    final googleUser = await googleSignIn.signIn();
    if (googleUser == null) {
      throw Exception('Google Sign-In was cancelled');
    }

    final googleAuth = await googleUser.authentication;
    final accessToken = googleAuth.accessToken;
    final idToken = googleAuth.idToken;

    if (accessToken == null) {
      throw Exception('No Access Token found');
    }
    if (idToken == null) {
      throw Exception('No ID Token found');
    }

    return client.auth.signInWithIdToken(
      provider: OAuthProvider.google,
      idToken: idToken,
      accessToken: accessToken,
    );
  }

  /// Send password reset email
  static Future<void> resetPassword({required String email}) async {
    await client.auth.resetPasswordForEmail(email);
  }

  /// Check if user is logged in
  static bool get isLoggedIn => currentUser != null;

  /// Listen to auth state changes
  static Stream<AuthState> get authStateChanges =>
      client.auth.onAuthStateChange;

  // ============================================================================
  // PROFILE OPERATIONS
  // ============================================================================

  /// Get current user's profile
  static Future<Map<String, dynamic>?> getProfile() async {
    if (userId == null) return null;

    final response = await client
        .from(SupabaseConfig.profilesTable)
        .select()
        .eq('id', userId!)
        .single();

    return response;
  }

  /// Update user profile
  static Future<void> updateProfile({
    String? fullName,
    String? skinType,
    String? gender,
    DateTime? dateOfBirth,
    List<String>? allergies,
    String? medicalHistory,
    String? trackingPreference,
  }) async {
    if (userId == null) return;

    final updates = <String, dynamic>{};
    if (fullName != null) updates['full_name'] = fullName;
    if (skinType != null) updates['skin_type'] = skinType;
    if (gender != null) updates['gender'] = gender;
    if (allergies != null) updates['allergies'] = allergies;
    if (medicalHistory != null) updates['medical_history'] = medicalHistory;
    if (trackingPreference != null) {
      updates['tracking_preference'] = trackingPreference;
    }
    if (dateOfBirth != null) {
      updates['date_of_birth'] = dateOfBirth.toIso8601String();
    }

    if (updates.isNotEmpty) {
      await client
          .from(SupabaseConfig.profilesTable)
          .update(updates)
          .eq('id', userId!);
    }
  }

  // ============================================================================
  // CHAT OPERATIONS
  // ============================================================================

  /// Create a new chat session
  static Future<Map<String, dynamic>> createChatSession({String? title}) async {
    final response = await client
        .from(SupabaseConfig.chatSessionsTable)
        .insert({'user_id': userId, 'title': title ?? 'New Conversation'})
        .select()
        .single();

    return response;
  }

  /// Get all chat sessions for current user
  static Future<List<Map<String, dynamic>>> getChatSessions() async {
    if (userId == null) return [];

    final response = await client
        .from(SupabaseConfig.chatSessionsTable)
        .select()
        .eq('user_id', userId!)
        .order('updated_at', ascending: false);

    return List<Map<String, dynamic>>.from(response);
  }

  /// Save a chat message
  static Future<Map<String, dynamic>> saveChatMessage({
    required String sessionId,
    required String sender,
    required String message,
    String? predictedDisease,
    double? confidence,
    String? confidenceLevel,
    String? modelUsed,
    List<Map<String, dynamic>>? treatments,
    List<String>? followUpQuestions,
    bool needsMoreInfo = false,
  }) async {
    final response = await client
        .from(SupabaseConfig.chatMessagesTable)
        .insert({
          'session_id': sessionId,
          'user_id': userId,
          'sender': sender,
          'message': message,
          'predicted_disease': predictedDisease,
          'confidence': confidence,
          'confidence_level': confidenceLevel,
          'model_used': modelUsed,
          'treatments': treatments,
          'follow_up_questions': followUpQuestions,
          'needs_more_info': needsMoreInfo,
        })
        .select()
        .single();

    return response;
  }

  /// Get messages for a chat session
  static Future<List<Map<String, dynamic>>> getChatMessages(
    String sessionId,
  ) async {
    final response = await client
        .from(SupabaseConfig.chatMessagesTable)
        .select()
        .eq('session_id', sessionId)
        .order('created_at', ascending: true);

    return List<Map<String, dynamic>>.from(response);
  }

  // ============================================================================
  // TRACKING JOURNEY OPERATIONS
  // ============================================================================

  /// Start a new tracking journey
  static Future<Map<String, dynamic>> startJourney({
    required String title,
    required String bodyPart,
    String? frequency,
    String? initialDiagnosis,
  }) async {
    final response = await client.from('tracking_journeys').insert({
      'user_id': userId,
      'title': title,
      'body_part': bodyPart,
      'frequency': frequency ?? 'weekly',
      'initial_diagnosis': initialDiagnosis,
    }).select().single();
    return response;
  }

  /// Get all tracking journeys for current user
  static Future<List<Map<String, dynamic>>> getJourneys() async {
    if (userId == null) return [];
    final response = await client
        .from('tracking_journeys')
        .select()
        .eq('user_id', userId!)
        .order('created_at', ascending: false);
    return List<Map<String, dynamic>>.from(response);
  }

  /// Get analysis progress for a specific journey
  static Future<List<Map<String, dynamic>>> getJourneyProgress(String journeyId) async {
    final response = await client
        .from(SupabaseConfig.skinAnalysesTable)
        .select()
        .eq('journey_id', journeyId)
        .order('created_at', ascending: true);
    return List<Map<String, dynamic>>.from(response);
  }

  // ============================================================================
  // SKIN ANALYSIS OPERATIONS
  // ============================================================================

  /// Upload skin image and save analysis
  static Future<Map<String, dynamic>> saveSkinAnalysis({
    required File imageFile,
    required String predictedDisease,
    required double confidence,
    required String confidenceLevel,
    Map<String, dynamic>? allPredictions,
    List<Map<String, dynamic>>? treatments,
    String? bodyLocation,
    String? symptomsDescription,
    String? duration,
    String? journeyId,
    String? bodyPartDetected,
  }) async {
    // Upload image to storage
    final fileName = '$userId/${DateTime.now().millisecondsSinceEpoch}.jpg';
    final storagePath = await client.storage
        .from(SupabaseConfig.skinImagesBucket)
        .upload(fileName, imageFile);

    // Get public URL
    final imageUrl = client.storage
        .from(SupabaseConfig.skinImagesBucket)
        .getPublicUrl(fileName);

    // Save analysis record
    final response = await client
        .from(SupabaseConfig.skinAnalysesTable)
        .insert({
          'user_id': userId,
          'image_url': imageUrl,
          'image_storage_path': storagePath,
          'predicted_disease': predictedDisease,
          'confidence': confidence,
          'confidence_level': confidenceLevel,
          'all_predictions': allPredictions,
          'treatments': treatments,
          'body_location': bodyLocation,
          'symptoms_description': symptomsDescription,
          'duration': duration,
          'journey_id': journeyId,
          'body_part_detected': bodyPartDetected,
        })
        .select()
        .single();

    return response;
  }

  /// Get skin analysis history
  static Future<List<Map<String, dynamic>>> getSkinAnalyses({
    int limit = 20,
  }) async {
    if (userId == null) return [];

    final response = await client
        .from(SupabaseConfig.skinAnalysesTable)
        .select()
        .eq('user_id', userId!)
        .order('created_at', ascending: false)
        .limit(limit);

    return List<Map<String, dynamic>>.from(response);
  }

  // ============================================================================
  // DIAGNOSIS HISTORY OPERATIONS
  // ============================================================================

  /// Save a diagnosis to history
  static Future<Map<String, dynamic>> saveDiagnosis({
    required String diseaseName,
    required double confidence,
    required String diagnosisType,
    String? chatMessageId,
    String? skinAnalysisId,
    bool? userConfirmed,
    String? userNotes,
  }) async {
    final response = await client
        .from(SupabaseConfig.diagnosisHistoryTable)
        .insert({
          'user_id': userId,
          'disease_name': diseaseName,
          'confidence': confidence,
          'diagnosis_type': diagnosisType,
          'chat_message_id': chatMessageId,
          'skin_analysis_id': skinAnalysisId,
          'user_confirmed': userConfirmed,
          'user_notes': userNotes,
        })
        .select()
        .single();

    return response;
  }

  /// Get diagnosis history
  static Future<List<Map<String, dynamic>>> getDiagnosisHistory({
    int limit = 50,
  }) async {
    if (userId == null) return [];

    final response = await client
        .from(SupabaseConfig.diagnosisHistoryTable)
        .select()
        .eq('user_id', userId!)
        .order('created_at', ascending: false)
        .limit(limit);

    return List<Map<String, dynamic>>.from(response);
  }

  // ============================================================================
  // TREATMENT TRACKING OPERATIONS
  // ============================================================================

  /// Add a treatment to track
  static Future<Map<String, dynamic>> addTreatment({
    required String treatmentName,
    String? treatmentType,
    String? dosage,
    String? frequency,
    String? diagnosisId,
    String? notes,
  }) async {
    final response = await client
        .from(SupabaseConfig.treatmentTrackingTable)
        .insert({
          'user_id': userId,
          'treatment_name': treatmentName,
          'treatment_type': treatmentType,
          'dosage': dosage,
          'frequency': frequency,
          'diagnosis_id': diagnosisId,
          'notes': notes,
        })
        .select()
        .single();

    return response;
  }

  /// Update treatment status/effectiveness
  static Future<void> updateTreatment({
    required String treatmentId,
    String? status,
    int? effectivenessRating,
    String? sideEffects,
    String? notes,
    DateTime? endDate,
  }) async {
    final updates = <String, dynamic>{};
    if (status != null) updates['status'] = status;
    if (effectivenessRating != null) {
      updates['effectiveness_rating'] = effectivenessRating;
    }
    if (sideEffects != null) updates['side_effects'] = sideEffects;
    if (notes != null) updates['notes'] = notes;
    if (endDate != null) updates['end_date'] = endDate.toIso8601String();

    if (updates.isNotEmpty) {
      await client
          .from(SupabaseConfig.treatmentTrackingTable)
          .update(updates)
          .eq('id', treatmentId);
    }
  }

  /// Get active treatments
  static Future<List<Map<String, dynamic>>> getActiveTreatments() async {
    if (userId == null) return [];

    final response = await client
        .from(SupabaseConfig.treatmentTrackingTable)
        .select()
        .eq('user_id', userId!)
        .eq('status', 'active')
        .order('start_date', ascending: false);

    return List<Map<String, dynamic>>.from(response);
  }

  /// Get all treatments
  static Future<List<Map<String, dynamic>>> getAllTreatments({
    int limit = 50,
  }) async {
    if (userId == null) return [];

    final response = await client
        .from(SupabaseConfig.treatmentTrackingTable)
        .select()
        .eq('user_id', userId!)
        .order('created_at', ascending: false)
        .limit(limit);

    return List<Map<String, dynamic>>.from(response);
  }
}
