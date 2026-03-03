import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/api_service.dart';
import '../services/supabase_service.dart';
import '../utils/app_styles.dart';

class SeverityScreen extends StatefulWidget {
  const SeverityScreen({super.key});

  @override
  State<SeverityScreen> createState() => _SeverityScreenState();
}

class _SeverityScreenState extends State<SeverityScreen> {
  static const Color _teal = Color(0xFF1F7A8C);
  static const Color _tealDark = Color(0xFF145563);
  static const Color _gold = Color(0xFFC27B2A);
  static const Color _red = Color(0xFFD64550);

  XFile? _selectedImage;
  bool _isLoading = false;
  bool _trackProgress = true;
  Map<String, dynamic>? _result;

  Future<void> _pickImage(ImageSource source) async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: source);
    if (picked == null) return;
    setState(() {
      _selectedImage = picked;
      _result = null;
    });
  }

  Future<void> _analyzeSeverity() async {
    if (_selectedImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a face image first.')),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final bytes = await _selectedImage!.readAsBytes();
      final response = await ApiService.analyzeSeverity(
        bytes,
        _selectedImage!.name,
        track: _trackProgress,
        userId: SupabaseService.userId ?? 'anonymous',
      );
      if (!mounted) return;
      setState(() {
        _result = response;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Severity analysis failed: $e')));
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _reset() {
    setState(() {
      _selectedImage = null;
      _result = null;
      _trackProgress = true;
    });
  }

  double _toDouble(dynamic value) {
    if (value is num) return value.toDouble();
    return double.tryParse(value?.toString() ?? '') ?? 0.0;
  }

  Map<String, dynamic> _toMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) {
      return value.map((k, v) => MapEntry(k.toString(), v));
    }
    return {};
  }

  List<Map<String, dynamic>> _toMapList(dynamic value) {
    if (value is! List) return [];
    final output = <Map<String, dynamic>>[];
    for (final item in value) {
      if (item is Map) {
        output.add(item.map((k, v) => MapEntry(k.toString(), v)));
      }
    }
    return output;
  }

  Color _levelColor(String level) {
    final normalized = level.trim().toLowerCase();
    if (normalized == 'mild') return AppColors.success;
    if (normalized == 'moderate') return _gold;
    if (normalized == 'severe') return _red;
    return _teal;
  }

  Widget _sectionCard({
    required String title,
    required Widget child,
    String? subtitle,
    IconData icon = Icons.analytics_outlined,
    Color accent = _teal,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: AppDecor.softCard(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, size: 18, color: accent),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: AppTextStyles.subHeading.copyWith(fontSize: 17),
                ),
              ),
            ],
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 6),
            Text(subtitle, style: AppTextStyles.body),
          ],
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }

  Widget _buildUploadView() {
    return Column(
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            gradient: AppGradients.hero,
            borderRadius: BorderRadius.circular(20),
            boxShadow: const [
              BoxShadow(
                color: Color(0x1F145563),
                blurRadius: 14,
                offset: Offset(0, 8),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Face Skin Severity',
                style: AppTextStyles.heading.copyWith(
                  color: Colors.white,
                  fontSize: 24,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Upload one clear face image. The system extracts engineered skin features and predicts Mild, Moderate, or Severe.',
                style: AppTextStyles.body.copyWith(
                  color: Colors.white.withValues(alpha: 0.9),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        _sectionCard(
          title: 'Face Image',
          subtitle: 'Use frontal/near-frontal photo with good lighting.',
          icon: Icons.camera_alt_outlined,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              InkWell(
                onTap: () => _pickImage(ImageSource.gallery),
                borderRadius: BorderRadius.circular(14),
                child: Container(
                  width: double.infinity,
                  height: 260,
                  decoration: BoxDecoration(
                    color: const Color(0xFFF8FCFD),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: _selectedImage == null
                      ? Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.face_retouching_natural_outlined,
                              size: 54,
                              color: _teal.withValues(alpha: 0.9),
                            ),
                            const SizedBox(height: 10),
                            const Text(
                              'Tap to select selfie',
                              style: TextStyle(fontWeight: FontWeight.w600),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Supported: JPG, JPEG, PNG',
                              style: AppTextStyles.body,
                            ),
                          ],
                        )
                      : ClipRRect(
                          borderRadius: BorderRadius.circular(13),
                          child: kIsWeb
                              ? Image.network(
                                  _selectedImage!.path,
                                  fit: BoxFit.cover,
                                )
                              : Image.file(
                                  File(_selectedImage!.path),
                                  fit: BoxFit.cover,
                                ),
                        ),
                ),
              ),
              const SizedBox(height: 14),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: [
                  FilledButton.icon(
                    onPressed: () => _pickImage(ImageSource.camera),
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('Camera'),
                    style: FilledButton.styleFrom(backgroundColor: _tealDark),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => _pickImage(ImageSource.gallery),
                    icon: const Icon(Icons.photo_library_outlined),
                    label: const Text('Gallery'),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        _sectionCard(
          title: 'Tracking',
          subtitle: 'Enable weekly trend tracking for this user profile.',
          icon: Icons.timeline_outlined,
          child: SwitchListTile(
            value: _trackProgress,
            activeThumbColor: AppColors.primary,
            contentPadding: EdgeInsets.zero,
            title: Text(
              _trackProgress ? 'Tracking enabled' : 'Tracking disabled',
              style: AppTextStyles.bodyStrong,
            ),
            subtitle: Text(
              _trackProgress
                  ? 'New entries will be saved in visits history.'
                  : 'Only one-time analysis output will be returned.',
              style: AppTextStyles.caption,
            ),
            onChanged: (value) {
              setState(() => _trackProgress = value);
            },
          ),
        ),
        const SizedBox(height: 18),
        SizedBox(
          width: double.infinity,
          height: 52,
          child: FilledButton(
            onPressed: _isLoading ? null : _analyzeSeverity,
            child: _isLoading
                ? const SizedBox(
                    height: 22,
                    width: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.2,
                      color: Colors.white,
                    ),
                  )
                : const Text(
                    'Analyze Severity',
                    style: TextStyle(fontWeight: FontWeight.w700),
                  ),
          ),
        ),
      ],
    );
  }

  Widget _buildResultView() {
    final result = _result ?? {};
    final level = (result['severity_level'] ?? 'Moderate').toString();
    final score = _toDouble(result['severity_score']);
    final confidence = _toDouble(result['confidence']);
    final probabilities = _toMap(result['probabilities']);
    final thresholds = _toMap(result['thresholds']);
    final preprocessing = _toMap(result['preprocessing']);
    final featureVector = _toMap(result['feature_vector']);
    final normalizedFeatures = _toMap(result['normalized_features']);
    final tracking = _toMap(result['tracking']);
    final weeklyTrend = _toMapList(tracking['weekly_trend']);

    final levelColor = _levelColor(level);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            gradient: LinearGradient(
              colors: [levelColor, levelColor.withValues(alpha: 0.72)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Severity Level',
                style: AppTextStyles.caption.copyWith(color: Colors.white70),
              ),
              const SizedBox(height: 4),
              Text(
                level,
                style: AppTextStyles.heading.copyWith(
                  color: Colors.white,
                  fontSize: 34,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'Severity Score: ${score.toStringAsFixed(1)} / 100',
                style: AppTextStyles.bodyStrong.copyWith(color: Colors.white),
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: LinearProgressIndicator(
                  minHeight: 8,
                  value: (score / 100).clamp(0.0, 1.0),
                  backgroundColor: Colors.white.withValues(alpha: 0.26),
                  color: Colors.white,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        _sectionCard(
          title: 'Prediction Confidence',
          subtitle: 'RandomForest class probabilities.',
          icon: Icons.query_stats_outlined,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Top confidence: ${(confidence * 100).toStringAsFixed(1)}%',
                style: AppTextStyles.bodyStrong,
              ),
              const SizedBox(height: 10),
              ...probabilities.entries.map((entry) {
                final p = _toDouble(entry.value);
                return Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${entry.key}: ${(p * 100).toStringAsFixed(1)}%',
                        style: AppTextStyles.bodyStrong,
                      ),
                      const SizedBox(height: 6),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: LinearProgressIndicator(
                          minHeight: 7,
                          value: p.clamp(0.0, 1.0),
                          color: _teal,
                          backgroundColor: AppColors.backgroundAlt,
                        ),
                      ),
                    ],
                  ),
                );
              }),
            ],
          ),
        ),
        const SizedBox(height: 14),
        _sectionCard(
          title: 'Score Thresholds',
          subtitle: 'Metadata-driven grading boundaries.',
          icon: Icons.tune_outlined,
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _chip('q1: ${_toDouble(thresholds['q1']).toStringAsFixed(2)}'),
              _chip('q2: ${_toDouble(thresholds['q2']).toStringAsFixed(2)}'),
              _chip('Score: ${score.toStringAsFixed(2)}'),
            ],
          ),
        ),
        const SizedBox(height: 14),
        _sectionCard(
          title: 'Preprocessing',
          subtitle: 'Image quality and pipeline metadata.',
          icon: Icons.photo_filter_outlined,
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _chip('Normalization: ${preprocessing['normalization'] ?? '-'}'),
              _chip(
                'Face visible: ${preprocessing['face_visible'] ?? 'unknown'}',
              ),
              _chip('Face count: ${preprocessing['face_count'] ?? 'unknown'}'),
              _chip(
                'Input: ${_toMap(preprocessing['input_size'])['width'] ?? '-'}x${_toMap(preprocessing['input_size'])['height'] ?? '-'}',
              ),
              _chip(
                'Target: ${_toMap(preprocessing['target_size'])['width'] ?? '-'}x${_toMap(preprocessing['target_size'])['height'] ?? '-'}',
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        _sectionCard(
          title: 'Extracted Features',
          subtitle: 'Raw engineered values from the image.',
          icon: Icons.dataset_outlined,
          child: _buildFeatureTable(featureVector),
        ),
        const SizedBox(height: 14),
        _sectionCard(
          title: 'Normalized Features',
          subtitle: 'Min-max scaled values used for model input.',
          icon: Icons.stacked_bar_chart_outlined,
          child: _buildFeatureTable(normalizedFeatures),
        ),
        const SizedBox(height: 14),
        if ((_result?['tracking_enabled'] ?? false) == true)
          _sectionCard(
            title: 'Progress Tracking',
            subtitle: 'Weekly trend for this user id.',
            icon: Icons.timeline,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (tracking['visits_count'] != null)
                  Text(
                    'Visits: ${tracking['visits_count']} | Improvement: ${tracking['improvement_percent'] ?? 0}%',
                    style: AppTextStyles.bodyStrong,
                  ),
                const SizedBox(height: 8),
                if (weeklyTrend.isEmpty)
                  Text(
                    'No weekly trend available yet.',
                    style: AppTextStyles.body,
                  )
                else
                  ...weeklyTrend.map(
                    (row) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              row['week']?.toString() ?? '-',
                              style: AppTextStyles.bodyStrong,
                            ),
                          ),
                          Text(
                            _toDouble(
                              row['avg_severity_score'],
                            ).toStringAsFixed(1),
                            style: AppTextStyles.body,
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        const SizedBox(height: 20),
        SizedBox(
          width: double.infinity,
          height: 50,
          child: OutlinedButton.icon(
            onPressed: _reset,
            icon: const Icon(Icons.refresh),
            label: const Text('Analyze Another Photo'),
          ),
        ),
      ],
    );
  }

  Widget _chip(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.backgroundAlt,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Text(text, style: AppTextStyles.caption.copyWith(fontSize: 13)),
    );
  }

  Widget _buildFeatureTable(Map<String, dynamic> values) {
    if (values.isEmpty) {
      return Text('No data available.', style: AppTextStyles.body);
    }
    final entries = values.entries.toList();
    entries.sort((a, b) => a.key.compareTo(b.key));
    return Column(
      children: entries
          .map(
            (entry) => Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(10),
                color: const Color(0xFFF8FBFC),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      entry.key,
                      style: AppTextStyles.bodyStrong.copyWith(fontSize: 13.5),
                    ),
                  ),
                  Text(
                    _toDouble(entry.value).toStringAsFixed(4),
                    style: AppTextStyles.body.copyWith(fontSize: 13.5),
                  ),
                ],
              ),
            ),
          )
          .toList(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Severity Analysis')),
      body: Container(
        decoration: const BoxDecoration(gradient: AppGradients.page),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 20),
            child: _result == null ? _buildUploadView() : _buildResultView(),
          ),
        ),
      ),
    );
  }
}
