import 'package:flutter/material.dart';
import '../utils/app_styles.dart';

class ResultScreen extends StatefulWidget {
  final Map<String, dynamic> data;

  const ResultScreen({super.key, required this.data});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  @override
  Widget build(BuildContext context) {
    final Map<String, dynamic> data = widget.data;
    // Handle nested Master Report or flat response
    final Map<String, dynamic> diag = data.containsKey('diagnosis')
        ? Map<String, dynamic>.from(data['diagnosis'])
        : data;

    final String prediction = (diag['prediction'] ??
            diag['final_diagnosis'] ??
            diag['disease'] ??
            'Unknown')
        .toString();
    final double confidence = _toDouble(diag['confidence']);
    final String confidencePercent =
        (diag['confidence_percent']?.toString() ??
        '${(confidence * 100).toStringAsFixed(1)}%');
    final String confidenceLevel = _normalizeConfidenceLevel(
      diag['confidence_level']?.toString(),
      confidence,
    );
    final Color confidenceColor = _confidenceColor(confidenceLevel);

    final String? consistencyWarning = data['consistency_warning']?.toString();

    final String? transcript = diag['transcript']?.toString();
    final String? transcriptionStatus = diag['transcription_status']
        ?.toString();
    final String? transcriptionError = diag['transcription_error']?.toString();

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

    final String? diseaseExplanation = diag['disease_explanation']?.toString();

    final double symptomMatchScore = _toDouble(diag['symptom_match_score']);
    final String symptomMatchPercent =
        diag['symptom_match_percent']?.toString() ??
        '${(symptomMatchScore * 100).toStringAsFixed(0)}%';

    final List<String> expectedSymptoms = _normalizeStringList(
      diag['expected_symptoms'] ?? diag['symptoms'],
    );
    final List<String> extractedSymptoms = _normalizeStringList(
      diag['extracted_symptoms'],
    );
    final List<String> matchedSymptoms = _normalizeStringList(
      diag['matched_symptoms'],
    );
    final List<String> warnings = _normalizeStringList(diag['warnings']);
    final List<String> nextSteps = _normalizeStringList(
      diag['next_steps'] ?? diag['recommendations'],
    );

    final List<Map<String, dynamic>> treatments = _normalizeMapList(
      diag['treatments'] ?? diag['recommended_treatments'],
    );
    final Map<String, dynamic> routine = _normalizeMap(
      data['skin_profile'] ?? diag['routine'],
    );
    final Map<String, dynamic> severity = _normalizeMap(data['severity']);

    // Model diagnostics variables
    final String decisionMode =
        (diag['decision_mode'] ?? diag['mode'] ?? 'unknown').toString();
    final String modelUsed = (diag['model_used'] ?? diag['model'] ?? 'fused')
        .toString();
    final List<Map<String, dynamic>> top3 = _normalizePredictionList(
      diag['top_3'] ?? diag['top3'] ?? diag['predictions'],
    );

    // Individual model outputs for diagnostics
    final String? imageDisease = diag['image_disease']?.toString();
    final double imageConfidence = _toDouble(diag['image_confidence']);
    final String? textDisease = diag['text_disease']?.toString();
    final double textConfidence = _toDouble(diag['text_confidence']);
    final double imageWeight = _toDouble(diag['image_weight']);
    final double textWeight = _toDouble(diag['text_weight']);
    final double agreementScore = _toDouble(diag['agreement_score']);

    return Scaffold(
      appBar: AppBar(title: const Text('Analysis Result')),
      body: Container(
        decoration: BoxDecoration(gradient: AppGradients.page(context)),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 22),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeroCard(
                prediction: prediction,
                confidencePercent: confidencePercent,
                confidenceLevel: confidenceLevel,
                confidenceColor: confidenceColor,
              ),
              const SizedBox(height: 20),
              if (data['summary'] != null) ...[
                _buildSummarySection(data['summary']!),
                const SizedBox(height: 14),
              ],

              const SizedBox(height: 14),
              if (consistencyWarning != null) ...[
                _buildConsistencyAlert(consistencyWarning),
                const SizedBox(height: 14),
              ],
              if (severity.isNotEmpty && severity['face_detected'] == true) ...[
                _buildSeverityCard(severity),
                const SizedBox(height: 14),
              ],

              if (hasTranscript) ...[
                _buildSectionCard(
                  title: 'Voice Transcript',
                  icon: Icons.mic,
                  iconColor: AppColors.primary,
                  child: Text(
                    normalizedTranscript,
                    style: TextStyle(
                      fontSize: 15,
                      color: context.clrTextMain,
                    ),
                  ),
                ),
                const SizedBox(height: 14),
              ],
              if (showTranscriptIssue) ...[
                _buildSectionCard(
                  title: 'Voice Transcript',
                  icon: Icons.mic_off,
                  iconColor: AppColors.warning,
                  child: Text(
                    transcriptionError ??
                        (isPlaceholderTranscript
                            ? 'Voice note was not transcribed by the server. Try uploading a WAV file or check ffmpeg setup.'
                            : 'Voice note could not be transcribed. Try a clearer recording or upload a WAV file.'),
                    style: TextStyle(
                      fontSize: 15,
                      color: context.clrTextMain,
                    ),
                  ),
                ),
                const SizedBox(height: 14),
              ],
              _buildSymptomsSection(
                diseaseExplanation: diseaseExplanation,
                extractedSymptoms: extractedSymptoms,
                matchedSymptoms: matchedSymptoms,
                expectedSymptoms: expectedSymptoms,
                symptomMatchScore: symptomMatchScore,
              ),
              const SizedBox(height: 14),
              if (treatments.isNotEmpty) ...[
                _buildTreatmentSection(treatments),
                const SizedBox(height: 14),
              ],
              if (routine.isNotEmpty) ...[
                _buildRoutineSection(routine),
                const SizedBox(height: 14),
              ],
              if (nextSteps.isNotEmpty) ...[
                _buildActionSection(nextSteps),
                const SizedBox(height: 14),
              ],
              if (warnings.isNotEmpty) _buildWarningSection(warnings),
              _buildPredictionSection(top3),
              const SizedBox(height: 14),
              _buildModelDiagnostics(
                imageDisease: imageDisease,
                imageConfidence: imageConfidence,
                textDisease: textDisease,
                textConfidence: textConfidence,
                imageWeight: imageWeight,
                textWeight: textWeight,
                agreementScore: agreementScore,
              ),
            ],
          ),
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
      padding: const EdgeInsets.all(28),
      decoration: BoxDecoration(
        gradient: AppGradients.premium,
        borderRadius: BorderRadius.circular(32),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.3),
            blurRadius: 25,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'AI ANALYSIS REPORT',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.6),
                  fontSize: 12,
                  letterSpacing: 2.0,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const Icon(
                Icons.verified_user_rounded,
                color: Colors.white,
                size: 20,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            prediction,
            style: AppTextStyles.heading(context).copyWith(
              color: Colors.white,
              fontSize: 34,
              height: 1.1,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.auto_graph_rounded, color: confidenceColor, size: 18),
                const SizedBox(width: 8),
                Text(
                  '$confidencePercent Confidence',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPredictionSection(List<Map<String, dynamic>> top3) {
    if (top3.isEmpty) return const SizedBox.shrink();
    return _buildSectionCard(
      title: 'Top Predictions',
      icon: Icons.insights_outlined,
      iconColor: AppColors.primaryDark,
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
                    backgroundColor: context.clrBorder.withValues(alpha: 0.7),
                    valueColor: const AlwaysStoppedAnimation<Color>(
                      AppColors.primaryDark,
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

  Widget _buildConsistencyAlert(String warning) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.warning.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.warning.withValues(alpha: 0.4)),
      ),
      child: Row(
        children: [
          const Icon(Icons.warning_amber_rounded, color: AppColors.warning, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              warning,
              style: TextStyle(
                fontSize: 14,
                color: context.clrTextMain,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSeverityCard(Map<String, dynamic> severity) {
    final String level =
        (severity['severity_label'] ?? severity['level'] ?? 'Unknown')
            .toString();
    final double score = _toDouble(
      severity['severity_score'] ?? severity['score'],
    );

    Color severityColor;
    switch (level.toLowerCase()) {
      case 'severe':
        severityColor = AppColors.error;
        break;
      case 'moderate':
        severityColor = AppColors.warning;
        break;
      default:
        severityColor = AppColors.success;
    }

    return _buildSectionCard(
      title: 'Severity Assessment',
      icon: Icons.assessment_outlined,
      iconColor: severityColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: severityColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  level.toUpperCase(),
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: severityColor,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Text(
                'Score: ${(score * 100).toStringAsFixed(1)}%',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: context.clrTextSec,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: score.clamp(0.0, 1.0),
              minHeight: 10,
              backgroundColor: context.clrBorder,
              valueColor: AlwaysStoppedAnimation<Color>(severityColor),
            ),
          ),
        ],
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
      final String safeTextValue =
          (textDisease == 'Unknown' && textConfidence <= 0.0)
              ? 'Not provided'
              : '$textDisease (${(textConfidence * 100).toStringAsFixed(1)}%)';
      rows.add(
        _buildKeyValueRow(
          label: 'Text Branch',
          value: safeTextValue,
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
      iconColor: AppColors.primaryDark,
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
      iconColor: AppColors.primary,
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
              backgroundColor: context.clrBorder.withValues(alpha: 0.6),
              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.accent),
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
      iconColor: AppColors.success,
      child: Column(
        children: treatments.map((item) {
          final String medicine = item['medicine']?.toString() ?? 'Medication';
          final String advice = item['advice']?.toString() ?? '';
          return Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.success.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: AppColors.success.withValues(alpha: 0.28),
              ),
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
      iconColor: AppColors.secondary,
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
      iconColor: AppColors.primary,
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
                        color: AppColors.primary,
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

  Widget _buildSummarySection(String summary) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.auto_awesome,
                color: AppColors.primary,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                'AI SUMMARY',
                style: TextStyle(
                  fontWeight: FontWeight.w900,
                  fontSize: 12,
                  letterSpacing: 1.2,
                  color: AppColors.primary.withValues(alpha: 0.8),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            summary,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: context.clrTextMain,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWarningSection(List<String> warnings) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.error.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(14),
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
      padding: const EdgeInsets.all(20),
      margin: const EdgeInsets.only(bottom: 14),
      decoration: AppDecor.softCard(context, radius: 28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: iconColor.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(icon, color: iconColor, size: 22),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Text(
                  title,
                  style: AppTextStyles.subHeading(context).copyWith(fontSize: 18),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
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
        color: context.clrSurface.withValues(alpha: 0.92),
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
                style: TextStyle(
                  fontSize: 11,
                  color: context.clrTextSec,
                ),
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

  Widget _buildKeyValueRow({required String label, required String value}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$label: ',
            style: TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 14,
              color: context.clrTextSec,
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 14,
                color: context.clrTextMain,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Text(
      text,
      style: TextStyle(
        fontWeight: FontWeight.w800,
        fontSize: 13,
        color: context.clrTextSec,
        letterSpacing: 0.5,
      ),
    );
  }

  Widget _buildMutedText(String text) {
    return Text(
      text,
      style: TextStyle(
        color: context.clrTextSec.withValues(alpha: 0.7),
        fontSize: 14,
        fontStyle: FontStyle.italic,
      ),
    );
  }

  Widget _buildSymptomChip(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  double _toDouble(dynamic value) {
    if (value is num) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? 0.0;
    return 0.0;
  }

  String _normalizeConfidenceLevel(String? level, double confidence) {
    if (level != null && level.isNotEmpty) return level;
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.5) return 'Moderate';
    return 'Low';
  }

  Color _confidenceColor(String level) {
    switch (level.toLowerCase()) {
      case 'high':
        return AppColors.success;
      case 'moderate':
        return AppColors.warning;
      case 'low':
        return AppColors.error;
      default:
        return AppColors.primary;
    }
  }

  List<String> _normalizeStringList(dynamic value) {
    if (value is List) return value.map((e) => e.toString()).toList();
    if (value is String) {
      if (value.startsWith('[') && value.endsWith(']')) {
        // Simple cleanup for stringified lists if any
        return value
            .substring(1, value.length - 1)
            .split(',')
            .map((e) => e.trim().replaceAll("'", "").replaceAll("\"", ""))
            .toList();
      }
      return [value];
    }
    return [];
  }

  List<Map<String, dynamic>> _normalizeMapList(dynamic value) {
    if (value is List) {
      return value
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList();
    }
    return [];
  }

  List<Map<String, dynamic>> _normalizePredictionList(dynamic value) {
    if (value is List) {
      return value
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList();
    }
    if (value is Map) {
      return value.entries
          .map((e) => {'disease': e.key, 'probability': _toDouble(e.value)})
          .toList();
    }
    return [];
  }

  Map<String, dynamic> _normalizeMap(dynamic value) {
    if (value is Map) return Map<String, dynamic>.from(value);
    return {};
  }
}
