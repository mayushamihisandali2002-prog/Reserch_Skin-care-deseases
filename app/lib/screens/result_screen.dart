import 'package:flutter/material.dart';
import '../utils/app_styles.dart';

class ResultScreen extends StatelessWidget {
  final Map<String, dynamic> data;

  const ResultScreen({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final String prediction =
        (data['prediction'] ?? data['final_diagnosis'] ?? 'Unknown').toString();
    final double confidence = _toDouble(data['confidence']);
    final String confidencePercent =
        (data['confidence_percent']?.toString() ??
        '${(confidence * 100).toStringAsFixed(1)}%');
    final String confidenceLevel = _normalizeConfidenceLevel(
      data['confidence_level']?.toString(),
      confidence,
    );
    final Color confidenceColor = _confidenceColor(confidenceLevel);

    final String? transcript = data['transcript']?.toString();
    final String? transcriptionStatus = data['transcription_status']
        ?.toString();
    final String? transcriptionError = data['transcription_error']?.toString();

    final String normalizedTranscript = (transcript ?? '').trim();
    final bool isPlaceholderTranscript =
        normalizedTranscript.toLowerCase() == 'skin condition';
    final bool hasTranscript =
        normalizedTranscript.isNotEmpty && !isPlaceholderTranscript;
    final bool showTranscriptIssue =
        !hasTranscript &&
        (isPlaceholderTranscript ||
            (transcriptionStatus != null &&
                transcriptionStatus != 'not_requested' &&
                transcriptionStatus != 'frontend_text'));

    final String? diseaseExplanation = data['disease_explanation']?.toString();
    final String decisionMode = (data['decision_mode']?.toString() ?? 'UNKNOWN')
        .toUpperCase();
    final String modelUsed = (data['model_used']?.toString() ?? 'unknown')
        .toUpperCase();

    final double symptomMatchScore = _toDouble(data['symptom_match_score']);
    final String symptomMatchPercent =
        data['symptom_match_percent']?.toString() ??
        '${(symptomMatchScore * 100).toStringAsFixed(0)}%';

    final List<String> expectedSymptoms = _normalizeStringList(
      data['expected_symptoms'] ?? data['symptoms'],
    );
    final List<String> extractedSymptoms = _normalizeStringList(
      data['extracted_symptoms'],
    );
    final List<String> matchedSymptoms = _normalizeStringList(
      data['matched_symptoms'],
    );
    final List<String> warnings = _normalizeStringList(data['warnings']);
    final List<String> nextSteps = _normalizeStringList(data['next_steps']);

    final List<Map<String, dynamic>> top3 = _normalizePredictionList(
      data['top3_predictions'],
    );
    final List<Map<String, dynamic>> treatments = _normalizeMapList(
      data['treatments'],
    );
    final Map<String, dynamic> routine = _normalizeMap(data['routine']);

    final String? imageDisease = _nullableString(data['image_disease']);
    final String? textDisease = _nullableString(data['text_disease']);
    final double imageConfidence = _toDouble(data['image_confidence']);
    final double textConfidence = _toDouble(data['text_confidence']);
    final double imageWeight = _toDouble(data['image_weight']);
    final double textWeight = _toDouble(data['text_weight']);
    final double agreementScore = _toDouble(data['agreement_score']);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis Result'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeroCard(
              prediction: prediction,
              confidencePercent: confidencePercent,
              confidenceLevel: confidenceLevel,
              confidenceColor: confidenceColor,
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                _buildMetricChip(
                  label: 'Confidence',
                  value: confidencePercent,
                  color: confidenceColor,
                  icon: Icons.analytics_outlined,
                ),
                _buildMetricChip(
                  label: 'Symptom Match',
                  value: symptomMatchPercent,
                  color: Colors.teal,
                  icon: Icons.fact_check_outlined,
                ),
                _buildMetricChip(
                  label: 'Decision',
                  value: _friendlyDecisionMode(decisionMode),
                  color: Colors.deepPurple,
                  icon: Icons.account_tree_outlined,
                ),
                _buildMetricChip(
                  label: 'Model',
                  value: modelUsed,
                  color: Colors.indigo,
                  icon: Icons.memory_outlined,
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (top3.isNotEmpty) ...[
              _buildPredictionSection(top3),
              const SizedBox(height: 16),
            ],
            if (imageDisease != null || textDisease != null) ...[
              _buildModelDiagnostics(
                imageDisease: imageDisease,
                imageConfidence: imageConfidence,
                textDisease: textDisease,
                textConfidence: textConfidence,
                imageWeight: imageWeight,
                textWeight: textWeight,
                agreementScore: agreementScore,
              ),
              const SizedBox(height: 16),
            ],
            if (hasTranscript) ...[
              _buildSectionCard(
                title: 'Voice Transcript',
                icon: Icons.mic,
                iconColor: Colors.blue,
                child: Text(
                  normalizedTranscript,
                  style: const TextStyle(fontSize: 15, color: Colors.black87),
                ),
              ),
              const SizedBox(height: 16),
            ],
            if (showTranscriptIssue) ...[
              _buildSectionCard(
                title: 'Voice Transcript',
                icon: Icons.mic_off,
                iconColor: Colors.orange,
                child: Text(
                  transcriptionError ??
                      (isPlaceholderTranscript
                          ? 'Voice note was not transcribed by the server. Try uploading a WAV file or check ffmpeg setup.'
                          : 'Voice note could not be transcribed. Try a clearer recording or upload a WAV file.'),
                  style: const TextStyle(fontSize: 15, color: Colors.black87),
                ),
              ),
              const SizedBox(height: 16),
            ],
            _buildSymptomsSection(
              diseaseExplanation: diseaseExplanation,
              extractedSymptoms: extractedSymptoms,
              matchedSymptoms: matchedSymptoms,
              expectedSymptoms: expectedSymptoms,
              symptomMatchScore: symptomMatchScore,
            ),
            const SizedBox(height: 16),
            if (treatments.isNotEmpty) ...[
              _buildTreatmentSection(treatments),
              const SizedBox(height: 16),
            ],
            if (routine.isNotEmpty) ...[
              _buildRoutineSection(routine),
              const SizedBox(height: 16),
            ],
            if (nextSteps.isNotEmpty) ...[
              _buildActionSection(nextSteps),
              const SizedBox(height: 16),
            ],
            if (warnings.isNotEmpty) _buildWarningSection(warnings),
          ],
        ),
      ),
    );
  }

  Widget _buildHeroCard({
    required String prediction,
    required String confidencePercent,
    required String confidenceLevel,
    required Color confidenceColor,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.primary,
            AppColors.primary.withValues(alpha: 0.82),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withValues(alpha: 0.24),
            blurRadius: 14,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Final Diagnosis',
            style: TextStyle(color: Colors.white70, fontSize: 13),
          ),
          const SizedBox(height: 6),
          Text(
            prediction,
            style: AppTextStyles.heading.copyWith(
              color: Colors.white,
              fontSize: 32,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _buildPill(
                label: 'Confidence $confidencePercent',
                textColor: Colors.white,
                backgroundColor: Colors.white.withValues(alpha: 0.2),
              ),
              _buildPill(
                label: confidenceLevel.toUpperCase(),
                textColor: confidenceColor,
                backgroundColor: Colors.white,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPredictionSection(List<Map<String, dynamic>> top3) {
    return _buildSectionCard(
      title: 'Top Predictions',
      icon: Icons.insights_outlined,
      iconColor: Colors.indigo,
      child: Column(
        children: top3.map((entry) {
          final String disease = entry['disease']?.toString() ?? 'Unknown';
          final double probability = _toDouble(entry['probability']);
          return Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        disease,
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          color: Colors.black87,
                        ),
                      ),
                    ),
                    Text(
                      '${(probability * 100).toStringAsFixed(1)}%',
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        color: Colors.black54,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: LinearProgressIndicator(
                    value: probability.clamp(0.0, 1.0),
                    minHeight: 9,
                    backgroundColor: Colors.grey.withValues(alpha: 0.2),
                    valueColor: AlwaysStoppedAnimation<Color>(
                      AppColors.primary,
                    ),
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildModelDiagnostics({
    required String? imageDisease,
    required double imageConfidence,
    required String? textDisease,
    required double textConfidence,
    required double imageWeight,
    required double textWeight,
    required double agreementScore,
  }) {
    final List<Widget> rows = [];

    if (imageDisease != null && imageDisease.isNotEmpty) {
      rows.add(
        _buildKeyValueRow(
          label: 'Image Branch',
          value:
              '$imageDisease (${(imageConfidence * 100).toStringAsFixed(1)}%)',
        ),
      );
    }
    if (textDisease != null && textDisease.isNotEmpty) {
      rows.add(
        _buildKeyValueRow(
          label: 'Text Branch',
          value: '$textDisease (${(textConfidence * 100).toStringAsFixed(1)}%)',
        ),
      );
    }
    if (imageWeight > 0 || textWeight > 0) {
      rows.add(
        _buildKeyValueRow(
          label: 'Fusion Weights',
          value:
              'Image ${(imageWeight * 100).toStringAsFixed(0)}% / Text ${(textWeight * 100).toStringAsFixed(0)}%',
        ),
      );
    }
    if (agreementScore > 0) {
      rows.add(
        _buildKeyValueRow(
          label: 'Branch Agreement',
          value: '${(agreementScore * 100).toStringAsFixed(0)}%',
        ),
      );
    }

    if (rows.isEmpty) {
      return const SizedBox.shrink();
    }

    return _buildSectionCard(
      title: 'Model Diagnostics',
      icon: Icons.tune,
      iconColor: Colors.blueGrey,
      child: Column(children: rows),
    );
  }

  Widget _buildSymptomsSection({
    required String? diseaseExplanation,
    required List<String> extractedSymptoms,
    required List<String> matchedSymptoms,
    required List<String> expectedSymptoms,
    required double symptomMatchScore,
  }) {
    return _buildSectionCard(
      title: 'Disease Information',
      icon: Icons.info_outline,
      iconColor: Colors.deepPurple,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (diseaseExplanation != null && diseaseExplanation.isNotEmpty) ...[
            Text(
              diseaseExplanation,
              style: const TextStyle(fontSize: 15, color: Colors.black87),
            ),
            const SizedBox(height: 12),
          ],
          _buildKeyValueRow(
            label: 'Symptom Match Quality',
            value: '${(symptomMatchScore * 100).toStringAsFixed(0)}%',
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: symptomMatchScore.clamp(0.0, 1.0),
              minHeight: 8,
              backgroundColor: Colors.grey.withValues(alpha: 0.2),
              valueColor: const AlwaysStoppedAnimation<Color>(Colors.teal),
            ),
          ),
          const SizedBox(height: 12),
          _buildLabel('Extracted Symptoms'),
          const SizedBox(height: 6),
          extractedSymptoms.isEmpty
              ? _buildMutedText('Not available')
              : Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: extractedSymptoms
                      .map((s) => _buildSymptomChip(s, Colors.indigo))
                      .toList(),
                ),
          const SizedBox(height: 10),
          _buildLabel('Matched Symptoms'),
          const SizedBox(height: 6),
          matchedSymptoms.isEmpty
              ? _buildMutedText('No direct symptom overlap detected')
              : Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: matchedSymptoms
                      .map((s) => _buildSymptomChip(s, Colors.green))
                      .toList(),
                ),
          const SizedBox(height: 10),
          _buildLabel('Expected Symptoms'),
          const SizedBox(height: 6),
          expectedSymptoms.isEmpty
              ? _buildMutedText('Not available')
              : Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: expectedSymptoms
                      .map((s) => _buildSymptomChip(s, Colors.blueGrey))
                      .toList(),
                ),
        ],
      ),
    );
  }

  Widget _buildTreatmentSection(List<Map<String, dynamic>> treatments) {
    return _buildSectionCard(
      title: 'Treatment Suggestions',
      icon: Icons.medication_outlined,
      iconColor: Colors.green,
      child: Column(
        children: treatments.map((item) {
          final String medicine = item['medicine']?.toString() ?? 'Medication';
          final String advice = item['advice']?.toString() ?? '';
          return Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.green.withValues(alpha: 0.06),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.green.withValues(alpha: 0.25)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  medicine,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    color: Colors.black87,
                  ),
                ),
                if (advice.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  Text(
                    advice,
                    style: const TextStyle(color: Colors.black87, height: 1.35),
                  ),
                ],
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildRoutineSection(Map<String, dynamic> routine) {
    final String morning = routine['morning']?.toString() ?? '';
    final String night = routine['night']?.toString() ?? '';
    final String treatment = routine['treatment']?.toString() ?? '';

    if (morning.isEmpty && night.isEmpty && treatment.isEmpty) {
      return const SizedBox.shrink();
    }

    return _buildSectionCard(
      title: 'Daily Routine',
      icon: Icons.calendar_today_outlined,
      iconColor: Colors.deepOrange,
      child: Column(
        children: [
          if (morning.isNotEmpty)
            _buildKeyValueRow(label: 'Morning', value: morning),
          if (night.isNotEmpty) _buildKeyValueRow(label: 'Night', value: night),
          if (treatment.isNotEmpty)
            _buildKeyValueRow(label: 'Treatment', value: treatment),
        ],
      ),
    );
  }

  Widget _buildActionSection(List<String> nextSteps) {
    return _buildSectionCard(
      title: 'Recommended Next Steps',
      icon: Icons.checklist_rtl,
      iconColor: Colors.blue,
      child: Column(
        children: nextSteps
            .map(
              (step) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Padding(
                      padding: EdgeInsets.only(top: 2),
                      child: Icon(
                        Icons.chevron_right,
                        size: 18,
                        color: Colors.blue,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        step,
                        style: const TextStyle(
                          color: Colors.black87,
                          height: 1.35,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            )
            .toList(),
      ),
    );
  }

  Widget _buildWarningSection(List<String> warnings) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.error.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.error.withValues(alpha: 0.45)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.warning_amber_rounded,
            color: AppColors.error,
            size: 24,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              warnings.join('\n'),
              style: const TextStyle(
                color: AppColors.error,
                fontWeight: FontWeight.w600,
                height: 1.35,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionCard({
    required String title,
    required IconData icon,
    required Color iconColor,
    required Widget child,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withValues(alpha: 0.10),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: iconColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: iconColor, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          child,
        ],
      ),
    );
  }

  Widget _buildMetricChip({
    required String label,
    required String value,
    required Color color,
    required IconData icon,
  }) {
    return Container(
      constraints: const BoxConstraints(minWidth: 120),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withValues(alpha: 0.28)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 6),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(fontSize: 11, color: Colors.black54),
              ),
              Text(
                value,
                style: TextStyle(
                  fontWeight: FontWeight.w700,
                  color: color,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPill({
    required String label,
    required Color textColor,
    required Color backgroundColor,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: textColor,
          fontWeight: FontWeight.w700,
          fontSize: 11,
        ),
      ),
    );
  }

  Widget _buildSymptomChip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          color: color,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  Widget _buildKeyValueRow({required String label, required String value}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 118,
            child: Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                color: Colors.black54,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(color: Colors.black87, height: 1.35),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Text(
      text,
      style: const TextStyle(
        fontWeight: FontWeight.w700,
        color: Colors.black87,
      ),
    );
  }

  Widget _buildMutedText(String text) {
    return Text(text, style: const TextStyle(color: Colors.black54));
  }

  static double _toDouble(dynamic value) {
    if (value == null) return 0.0;
    if (value is num) return value.toDouble();
    return double.tryParse(value.toString()) ?? 0.0;
  }

  static String? _nullableString(dynamic value) {
    if (value == null) return null;
    final parsed = value.toString().trim();
    return parsed.isEmpty || parsed.toLowerCase() == 'none' ? null : parsed;
  }

  static Map<String, dynamic> _normalizeMap(dynamic value) {
    if (value is Map<String, dynamic>) {
      return value;
    }
    if (value is Map) {
      return value.map((k, v) => MapEntry(k.toString(), v));
    }
    return {};
  }

  static List<Map<String, dynamic>> _normalizeMapList(dynamic value) {
    if (value is! List) return [];
    return value
        .whereType<Map>()
        .map((e) => e.map((k, v) => MapEntry(k.toString(), v)))
        .toList();
  }

  static List<Map<String, dynamic>> _normalizePredictionList(dynamic value) {
    return _normalizeMapList(value);
  }

  static List<String> _normalizeStringList(dynamic value) {
    if (value is! List) return [];
    return value
        .where((item) => item != null)
        .map((item) => item.toString().trim())
        .where((item) => item.isNotEmpty)
        .toList();
  }

  static String _normalizeConfidenceLevel(String? provided, double confidence) {
    final raw = provided?.trim().toLowerCase();
    if (raw == 'high' || raw == 'moderate' || raw == 'medium' || raw == 'low') {
      return raw == 'medium' ? 'moderate' : raw!;
    }
    if (confidence >= 0.75) return 'high';
    if (confidence >= 0.50) return 'moderate';
    return 'low';
  }

  static Color _confidenceColor(String level) {
    switch (level.toLowerCase()) {
      case 'high':
        return AppColors.success;
      case 'moderate':
        return Colors.orange;
      default:
        return AppColors.error;
    }
  }

  static String _friendlyDecisionMode(String mode) {
    return mode
        .split('_')
        .where((p) => p.isNotEmpty)
        .map((p) => p[0] + p.substring(1).toLowerCase())
        .join(' ');
  }
}
