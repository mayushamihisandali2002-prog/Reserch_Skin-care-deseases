import 'dart:io';

import 'package:app/components/skin_type_skincare_recommendation/data/skin_care_api.dart';
import 'package:app/utils/app_styles.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

class SkinCareScreen extends StatefulWidget {
  const SkinCareScreen({super.key});

  @override
  State<SkinCareScreen> createState() => _SkinCareScreenState();
}

class _SkinCareScreenState extends State<SkinCareScreen> {
  // Using getters for theme-aware brand colors
  Color get _brand => AppColors.primary;
  Color get _brandDark => AppColors.primaryDark;
  Color get _positive => AppColors.success;
  Color get _warning => AppColors.warning;
  Color get _danger => AppColors.error;
  Color get _border => context.clrBorder;

  XFile? _selectedImage;
  bool _isLoading = false;
  Map<String, dynamic>? _analysisResult;

  final Set<String> _selectedAllergies = <String>{};
  final Set<String> _selectedGoals = <String>{};

  String _routineLevel = 'simple';
  String _budget = 'medium';
  String _tightAfterWash = 'skip';
  String _shinyAfterHours = 'skip';

  static const Map<String, String> _allergyOptions = {
    'fragrance': 'Fragrance',
    'alcohol_denat': 'Alcohol Denat.',
    'essential_oils': 'Essential Oils',
    'niacinamide': 'Niacinamide',
    'salicylic_acid_bha': 'Salicylic Acid (BHA)',
    'aha': 'Glycolic/Lactic Acid (AHA)',
    'retinoids': 'Retinoids',
    'benzoyl_peroxide': 'Benzoyl Peroxide',
    'sunscreen_filters': 'Sunscreen Filters',
  };

  static const Map<String, String> _goalOptions = {
    'acne_pimples': 'Acne / Pimples',
    'oil_control': 'Oil Control',
    'dryness': 'Dryness',
    'redness_irritation': 'Redness/Irritation',
    'dark_spots': 'Dark Spots',
    'texture_pores': 'Texture / Pores',
    'wrinkles_anti_aging': 'Wrinkles / Anti-Aging',
  };

  static const Map<String, String> _routineOptions = {
    'simple': 'Simple (2-3 steps)',
    'full': 'Full routine',
  };

  static const Map<String, String> _budgetOptions = {
    'low': 'Low',
    'medium': 'Medium',
    'flexible': 'Flexible',
  };

  static const Map<String, String> _yesNoOptions = {
    'skip': 'Not sure (skip)',
    'yes': 'Yes',
    'no': 'No',
  };

  bool? _choiceToBool(String value) {
    if (value == 'yes') return true;
    if (value == 'no') return false;
    return null;
  }

  String _titleCaseFromSlug(String value) {
    final normalized = value.trim().replaceAll('_', ' ');
    if (normalized.isEmpty) return value;
    return normalized
        .split(' ')
        .where((part) => part.isNotEmpty)
        .map((part) => part[0].toUpperCase() + part.substring(1).toLowerCase())
        .join(' ');
  }

  String _resolveOptionLabel(Map<String, String> options, dynamic rawValue) {
    final value = rawValue?.toString().trim() ?? '';
    if (value.isEmpty) return 'Not provided';
    if (options.containsKey(value)) {
      return options[value]!;
    }

    final lowerValue = value.toLowerCase();
    for (final entry in options.entries) {
      if (entry.value.toLowerCase() == lowerValue) {
        return entry.value;
      }
    }

    return _titleCaseFromSlug(value);
  }

  String _yesNoLabel(dynamic value) {
    if (value == null) return _yesNoOptions['skip']!;
    if (value is bool) {
      return value ? _yesNoOptions['yes']! : _yesNoOptions['no']!;
    }

    final normalized = value.toString().trim().toLowerCase();
    if (normalized == 'yes' || normalized == 'true') {
      return _yesNoOptions['yes']!;
    }
    if (normalized == 'no' || normalized == 'false') {
      return _yesNoOptions['no']!;
    }
    return _yesNoOptions['skip']!;
  }

  double _toDouble(dynamic value) {
    if (value is num) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? 0.0;
    return 0.0;
  }

  bool _toBool(dynamic value) {
    if (value is bool) return value;
    if (value is num) return value != 0;
    final normalized = value?.toString().trim().toLowerCase() ?? '';
    return const {'true', '1', 'yes', 'y', 'required'}.contains(normalized);
  }

  List<String> _toStringList(dynamic value) {
    if (value is! List) return <String>[];
    return value
        .where((item) => item != null)
        .map((item) => item.toString().trim())
        .where((item) => item.isNotEmpty)
        .toList();
  }

  Map<String, dynamic> _toMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) {
      return value.map((k, v) => MapEntry(k.toString(), v));
    }
    return <String, dynamic>{};
  }

  Future<void> _pickImage(ImageSource source) async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: source);

    if (pickedFile != null) {
      setState(() {
        _selectedImage = pickedFile;
        _analysisResult = null;
      });
    }
  }

  Future<void> _analyzeSkin() async {
    if (_selectedImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please upload an image first.')),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final imageBytes = await _selectedImage!.readAsBytes();
      final fileName = _selectedImage!.name;

      final result = await SkinCareApi.analyze(
        imageBytes,
        fileName,
        allergies: _selectedAllergies.toList(),
        goals: _selectedGoals.toList(),
        routineLevel: _routineLevel,
        budget: _budget,
        tightAfterWash: _choiceToBool(_tightAfterWash),
        shinyAfter23h: _choiceToBool(_shinyAfterHours),
      );

      if (!mounted) return;
      setState(() {
        _analysisResult = result;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _toggleGoal(String key, bool selected) {
    setState(() {
      if (selected) {
        if (_selectedGoals.length >= 3) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Select up to 3 goals only.')),
          );
          return;
        }
        _selectedGoals.add(key);
      } else {
        _selectedGoals.remove(key);
      }
    });
  }

  void _resetAll() {
    setState(() {
      _selectedImage = null;
      _analysisResult = null;
      _selectedAllergies.clear();
      _selectedGoals.clear();
      _routineLevel = 'simple';
      _budget = 'medium';
      _tightAfterWash = 'skip';
      _shinyAfterHours = 'skip';
    });
  }

  Widget _buildSectionCard({
    required String title,
    required Widget child,
    String? subtitle,
    IconData? icon,
    Color? accentColor,
    EdgeInsetsGeometry padding = const EdgeInsets.all(16),
  }) {
    final effectiveAccent = accentColor ?? _brand;
    return Container(
      decoration: BoxDecoration(
        color: context.clrSurface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: _border),
        boxShadow: [
          BoxShadow(
            color: context.isDarkMode
                ? Colors.black26
                : Colors.black.withValues(alpha: 0.04),
            blurRadius: 14,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      padding: padding,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (icon != null) ...[
                Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(
                    color: effectiveAccent.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, size: 18, color: effectiveAccent),
                ),
                const SizedBox(width: 10),
              ],
              Expanded(
                child: Text(
                  title,
                  style: AppTextStyles.subHeading(
                    context,
                  ).copyWith(fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 6),
            Text(subtitle, style: AppTextStyles.body(context)),
          ],
          const SizedBox(height: 14),
          child,
        ],
      ),
    );
  }

  Widget _buildImagePreview() {
    return InkWell(
      onTap: () => _pickImage(ImageSource.gallery),
      borderRadius: BorderRadius.circular(16),
      child: Container(
        height: 260,
        width: double.infinity,
        decoration: BoxDecoration(
          color: context.clrBackground,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: _brand.withValues(alpha: 0.35), width: 1.4),
        ),
        child: _selectedImage == null
            ? Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.face_retouching_natural,
                    size: 56,
                    color: _brand.withValues(alpha: 0.9),
                  ),
                  const SizedBox(height: 10),
                  const Text(
                    'Tap to select a clear selfie',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Frontal face, good lighting, minimal filters',
                    style: AppTextStyles.body(context),
                    textAlign: TextAlign.center,
                  ),
                ],
              )
            : ClipRRect(
                borderRadius: BorderRadius.circular(15),
                child: kIsWeb
                    ? Image.network(_selectedImage!.path, fit: BoxFit.cover)
                    : Image.file(File(_selectedImage!.path), fit: BoxFit.cover),
              ),
      ),
    );
  }

  Widget _buildPhotoActions() {
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: [
        SizedBox(
          width: 180,
          child: FilledButton.icon(
            onPressed: () => _pickImage(ImageSource.camera),
            icon: const Icon(Icons.camera_alt_outlined),
            label: const Text('Use Camera'),
            style: FilledButton.styleFrom(
              backgroundColor: _brandDark,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ),
        SizedBox(
          width: 180,
          child: OutlinedButton.icon(
            onPressed: () => _pickImage(ImageSource.gallery),
            icon: const Icon(Icons.photo_library_outlined),
            label: const Text('Open Gallery'),
            style: OutlinedButton.styleFrom(
              foregroundColor: _brandDark,
              side: BorderSide(color: _brandDark.withValues(alpha: 0.38)),
              padding: const EdgeInsets.symmetric(vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCheckboxGroup({
    required String title,
    required String subtitle,
    required Map<String, String> options,
    required Set<String> selectedValues,
    required void Function(String key, bool value) onChanged,
    required IconData icon,
  }) {
    return _buildSectionCard(
      title: title,
      subtitle: subtitle,
      icon: icon,
      child: Column(
        children: options.entries.map((entry) {
          final selected = selectedValues.contains(entry.key);
          return Container(
            margin: const EdgeInsets.only(bottom: 10),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: selected
                    ? _brand.withValues(alpha: 0.35)
                    : _border.withValues(alpha: 0.9),
              ),
              color: selected
                  ? _brand.withValues(alpha: 0.08)
                  : context.clrSurface,
            ),
            child: CheckboxListTile(
              dense: true,
              value: selected,
              controlAffinity: ListTileControlAffinity.leading,
              activeColor: _brand,
              contentPadding: const EdgeInsets.symmetric(horizontal: 10),
              title: Text(
                entry.value,
                style: TextStyle(fontWeight: FontWeight.w500),
              ),
              onChanged: (value) => onChanged(entry.key, value ?? false),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildDropdownField({
    required String label,
    required String currentValue,
    required Map<String, String> options,
    required ValueChanged<String> onChanged,
  }) {
    return DropdownButtonFormField<String>(
      initialValue: currentValue,
      borderRadius: BorderRadius.circular(14),
      decoration: InputDecoration(
        labelText: label,
        filled: true,
        fillColor: context.clrSurface,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: _brand.withValues(alpha: 0.24)),
        ),
      ),
      items: options.entries
          .map(
            (entry) => DropdownMenuItem<String>(
              value: entry.key,
              child: Text(entry.value),
            ),
          )
          .toList(),
      onChanged: (value) {
        if (value == null) return;
        onChanged(value);
      },
    );
  }

  Widget _buildQuestionnaireCard() {
    return _buildSectionCard(
      title: 'Routine Preferences',
      subtitle: 'Use dropdowns only to keep the flow quick and consistent.',
      icon: Icons.tune,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final isWide = constraints.maxWidth > 780;
          if (!isWide) {
            return Column(
              children: [
                _buildDropdownField(
                  label: 'Routine Preference',
                  currentValue: _routineLevel,
                  options: _routineOptions,
                  onChanged: (value) => setState(() => _routineLevel = value),
                ),
                const SizedBox(height: 12),
                _buildDropdownField(
                  label: 'Budget',
                  currentValue: _budget,
                  options: _budgetOptions,
                  onChanged: (value) => setState(() => _budget = value),
                ),
                const SizedBox(height: 12),
                _buildDropdownField(
                  label: 'Does your skin feel tight after washing?',
                  currentValue: _tightAfterWash,
                  options: _yesNoOptions,
                  onChanged: (value) => setState(() => _tightAfterWash = value),
                ),
                const SizedBox(height: 12),
                _buildDropdownField(
                  label: 'Does your face get shiny within 2-3 hours?',
                  currentValue: _shinyAfterHours,
                  options: _yesNoOptions,
                  onChanged: (value) =>
                      setState(() => _shinyAfterHours = value),
                ),
              ],
            );
          }

          return Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: _buildDropdownField(
                      label: 'Routine Preference',
                      currentValue: _routineLevel,
                      options: _routineOptions,
                      onChanged: (value) =>
                          setState(() => _routineLevel = value),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildDropdownField(
                      label: 'Budget',
                      currentValue: _budget,
                      options: _budgetOptions,
                      onChanged: (value) => setState(() => _budget = value),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _buildDropdownField(
                      label: 'Skin feels tight after washing?',
                      currentValue: _tightAfterWash,
                      options: _yesNoOptions,
                      onChanged: (value) =>
                          setState(() => _tightAfterWash = value),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildDropdownField(
                      label: 'Face gets shiny within 2-3 hours?',
                      currentValue: _shinyAfterHours,
                      options: _yesNoOptions,
                      onChanged: (value) =>
                          setState(() => _shinyAfterHours = value),
                    ),
                  ),
                ],
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildAnalyzeButton() {
    return SizedBox(
      width: double.infinity,
      height: 54,
      child: FilledButton(
        onPressed: _isLoading ? null : _analyzeSkin,
        style: FilledButton.styleFrom(
          backgroundColor: _brandDark,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
        ),
        child: _isLoading
            ? const SizedBox(
                height: 22,
                width: 22,
                child: CircularProgressIndicator(
                  strokeWidth: 2.4,
                  color: Colors.white,
                ),
              )
            : const Text(
                'Analyze Skin',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
              ),
      ),
    );
  }

  Widget _buildInputView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            gradient: LinearGradient(
              colors: [
                _brand.withValues(alpha: 0.18),
                context.isDarkMode ? Colors.black26 : const Color(0xFFF4FBF8),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            border: Border.all(color: _brand.withValues(alpha: 0.28)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Personal Skin Care Assistant',
                style: AppTextStyles.heading(context).copyWith(fontSize: 22),
              ),
              const SizedBox(height: 8),
              Text(
                'Upload one selfie and choose dropdown/checkbox options. The app returns skin type, confidence, and a safety-filtered routine.',
                style: AppTextStyles.body(context).copyWith(height: 1.45),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),

        _buildSectionCard(
          title: 'Face Image',
          subtitle:
              'Use a clear front-facing photo in good lighting for best predictions.',
          icon: Icons.camera_enhance_outlined,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildImagePreview(),
              const SizedBox(height: 14),
              _buildPhotoActions(),
            ],
          ),
        ),
        const SizedBox(height: 16),

        _buildCheckboxGroup(
          title: 'Allergies / Sensitivities',
          subtitle: 'Select all that apply.',
          options: _allergyOptions,
          selectedValues: _selectedAllergies,
          icon: Icons.health_and_safety_outlined,
          onChanged: (key, value) {
            setState(() {
              if (value) {
                _selectedAllergies.add(key);
              } else {
                _selectedAllergies.remove(key);
              }
            });
          },
        ),
        const SizedBox(height: 16),

        _buildCheckboxGroup(
          title: 'Skin Concerns / Goals',
          subtitle: 'Choose up to 3 goals.',
          options: _goalOptions,
          selectedValues: _selectedGoals,
          icon: Icons.flag_outlined,
          onChanged: _toggleGoal,
        ),
        const SizedBox(height: 16),

        _buildQuestionnaireCard(),
        const SizedBox(height: 20),

        _buildAnalyzeButton(),
      ],
    );
  }

  Widget _buildResultHero(String skinType, double confidence) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        gradient: LinearGradient(
          colors: [_brand, _brandDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: [
          BoxShadow(
            color: _brandDark.withValues(alpha: 0.24),
            blurRadius: 16,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Predicted Skin Type',
                  style: AppTextStyles.body(context).copyWith(
                    color: Colors.white.withValues(alpha: 0.86),
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  skinType,
                  style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  'Confidence: ${(confidence * 100).toStringAsFixed(1)}%',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: LinearProgressIndicator(
                    value: confidence.clamp(0.0, 1.0),
                    minHeight: 8,
                    backgroundColor: Colors.white.withValues(alpha: 0.25),
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 14),
          Container(
            width: 78,
            height: 78,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.17),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white.withValues(alpha: 0.28)),
            ),
            child: Text(
              '${(confidence * 100).toStringAsFixed(0)}%',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w700,
                fontSize: 16,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildValidationBanner({
    required String validationStatus,
    required String analysisScope,
    required bool requiresReview,
    required bool questionnaireAdjusted,
    required List<String> reviewReasons,
  }) {
    final title = requiresReview
        ? 'Review recommended'
        : 'Operational guidance only';

    final message = validationStatus == 'operational_only_unlabeled'
        ? 'This skin-type model is running operationally, but there is no local labeled benchmark available for a formal accuracy claim.'
        : 'Use this output as cosmetic routine guidance only.';

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _warning.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: _warning.withValues(alpha: 0.32)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.info_outline, color: _warning),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  title,
                  style: AppTextStyles.bodyStrong(
                    context,
                  ).copyWith(color: context.clrTextMain),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(message, style: AppTextStyles.body(context)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _metaChip('Scope: ${_titleCaseFromSlug(analysisScope)}'),
              if (questionnaireAdjusted)
                _metaChip('Questionnaire adjusted final skin type'),
            ],
          ),
          if (reviewReasons.isNotEmpty) ...[
            const SizedBox(height: 10),
            ...reviewReasons.map(
              (reason) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.fiber_manual_record, size: 8, color: _warning),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(reason, style: AppTextStyles.body(context)),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildProbabilityCard(Map<String, dynamic> probabilities) {
    if (probabilities.isEmpty) {
      return const SizedBox.shrink();
    }

    final entries = probabilities.entries.toList()
      ..sort((a, b) => _toDouble(b.value).compareTo(_toDouble(a.value)));

    final topKey = entries.first.key;

    return _buildSectionCard(
      title: 'Class Probabilities',
      subtitle: 'All skin-type class scores from the model.',
      icon: Icons.analytics_outlined,
      accentColor: _brand,
      child: Wrap(
        spacing: 10,
        runSpacing: 10,
        children: entries.map((entry) {
          final probability = (_toDouble(entry.value) * 100).toStringAsFixed(1);
          final isTop = entry.key == topKey;
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
            decoration: BoxDecoration(
              color: isTop
                  ? _brand.withValues(alpha: 0.12)
                  : context.clrBackground,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: isTop
                    ? _brand.withValues(alpha: 0.44)
                    : _border.withValues(alpha: 0.9),
              ),
            ),
            child: Text(
              '${_titleCaseFromSlug(entry.key)}: $probability%',
              style: TextStyle(
                fontWeight: isTop ? FontWeight.w700 : FontWeight.w500,
                color: isTop
                    ? (context.isDarkMode ? AppColors.success : _brandDark)
                    : context.clrTextMain,
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildTagChips(
    List<String> values, {
    required Color color,
    required IconData icon,
  }) {
    if (values.isEmpty) {
      return Text('None selected', style: AppTextStyles.body(context));
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: values
          .map(
            (item) => Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: color.withValues(alpha: 0.28)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(icon, size: 14, color: color),
                  const SizedBox(width: 6),
                  Text(
                    item,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                ],
              ),
            ),
          )
          .toList(),
    );
  }

  Widget _buildInputSummaryCard({
    required List<String> goals,
    required List<String> allergies,
    required String routineLevel,
    required String budget,
    required String tightAfterWash,
    required String shinyAfterHours,
  }) {
    return _buildSectionCard(
      title: 'Your Inputs',
      subtitle: 'Selections used to personalize recommendations.',
      icon: Icons.fact_check_outlined,
      accentColor: _warning,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Goals',
            style: AppTextStyles.body(
              context,
            ).copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          _buildTagChips(goals, color: _positive, icon: Icons.flag),
          const SizedBox(height: 14),
          Text(
            'Allergies / Sensitivities',
            style: AppTextStyles.body(
              context,
            ).copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          _buildTagChips(
            allergies,
            color: _danger,
            icon: Icons.warning_amber_rounded,
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _metaChip('Routine: $routineLevel'),
              _metaChip('Budget: $budget'),
              _metaChip('Tight after wash: $tightAfterWash'),
              _metaChip('Shiny in 2-3h: $shinyAfterHours'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _metaChip(String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: context.clrBackground,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _border),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 13.5,
          fontWeight: FontWeight.w500,
          color: context.clrTextMain,
        ),
      ),
    );
  }

  Widget _buildIconList(
    List<String> values, {
    required IconData icon,
    required Color color,
    String emptyState = 'No items available',
  }) {
    if (values.isEmpty) {
      return Text(emptyState, style: AppTextStyles.body(context));
    }

    return Column(
      children: values
          .map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 9),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(icon, color: color, size: 18),
                  const SizedBox(width: 9),
                  Expanded(
                    child: Text(
                      item,
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w500,
                        color: context.clrTextMain,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          )
          .toList(),
    );
  }

  Widget _buildListCard({
    required String title,
    required List<String> items,
    required IconData sectionIcon,
    required IconData itemIcon,
    required Color color,
    String emptyState = 'No data available',
  }) {
    return _buildSectionCard(
      title: title,
      icon: sectionIcon,
      accentColor: color,
      child: _buildIconList(
        items,
        icon: itemIcon,
        color: color,
        emptyState: emptyState,
      ),
    );
  }

  Widget _buildTwoColumn({required Widget left, required Widget right}) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 900) {
          return Column(children: [left, const SizedBox(height: 14), right]);
        }

        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(child: left),
            const SizedBox(width: 14),
            Expanded(child: right),
          ],
        );
      },
    );
  }

  Widget _buildResultView() {
    final skinTypeRaw = (_analysisResult!['skin_type'] ?? 'unknown').toString();
    final skinType = _titleCaseFromSlug(skinTypeRaw);
    final confidence = _toDouble(
      _analysisResult!['skin_type_confidence'] ??
          _analysisResult!['confidence'],
    );

    final userInputs = _toMap(_analysisResult!['user_inputs']);
    final recommendations = _toMap(_analysisResult!['recommendations']);
    final probabilities = _toMap(_analysisResult!['probabilities']);

    final selectedGoals = _toStringList(
      userInputs['goals'],
    ).map((value) => _resolveOptionLabel(_goalOptions, value)).toList();
    final selectedAllergies = _toStringList(
      userInputs['allergies'],
    ).map((value) => _resolveOptionLabel(_allergyOptions, value)).toList();

    final safeIngredients = _toStringList(recommendations['safe_ingredients']);
    final avoidIngredients = _toStringList(
      recommendations['avoid_ingredients'],
    );

    final routine = _toMap(recommendations['routine']);
    final routineAM = _toStringList(routine['AM'] ?? routine['am']);
    final routinePM = _toStringList(routine['PM'] ?? routine['pm']);

    final routineLevel = _resolveOptionLabel(
      _routineOptions,
      userInputs['routine_level'] ??
          userInputs['routineLevel'] ??
          _routineLevel,
    );
    final budget = _resolveOptionLabel(
      _budgetOptions,
      userInputs['budget'] ?? _budget,
    );
    final tightAfterWash = _yesNoLabel(
      userInputs['tight_after_wash'] ?? userInputs['tightAfterWash'],
    );
    final shinyAfterHours = _yesNoLabel(
      userInputs['shiny_after_2_3h'] ?? userInputs['shinyAfter23h'],
    );

    final note =
        (_analysisResult!['note'] ??
                _analysisResult!['disclaimer'] ??
                'Cosmetic guidance only; not a medical diagnosis.')
            .toString();
    final validationStatus = (_analysisResult!['validation_status'] ?? '')
        .toString();
    final analysisScope = (_analysisResult!['analysis_scope'] ?? '').toString();
    final requiresReview = _toBool(_analysisResult!['requires_review']);
    final reviewReasons = _toStringList(_analysisResult!['review_reasons']);
    final limitations = _toStringList(_analysisResult!['limitations']);
    final nextSteps = _toStringList(_analysisResult!['next_steps']);
    final questionnaireAdjusted = _toBool(
      _analysisResult!['questionnaire_adjusted'],
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildResultHero(skinType, confidence),
        const SizedBox(height: 16),
        if (validationStatus.isNotEmpty ||
            requiresReview ||
            questionnaireAdjusted) ...[
          _buildValidationBanner(
            validationStatus: validationStatus,
            analysisScope: analysisScope,
            requiresReview: requiresReview,
            questionnaireAdjusted: questionnaireAdjusted,
            reviewReasons: reviewReasons,
          ),
          const SizedBox(height: 16),
        ],

        _buildProbabilityCard(probabilities),
        if (probabilities.isNotEmpty) const SizedBox(height: 16),

        _buildInputSummaryCard(
          goals: selectedGoals,
          allergies: selectedAllergies,
          routineLevel: routineLevel,
          budget: budget,
          tightAfterWash: tightAfterWash,
          shinyAfterHours: shinyAfterHours,
        ),
        const SizedBox(height: 16),

        _buildTwoColumn(
          left: _buildListCard(
            title: 'Safe Ingredients',
            items: safeIngredients,
            sectionIcon: Icons.verified_user_outlined,
            itemIcon: Icons.spa,
            color: _positive,
            emptyState: 'No safe ingredient list provided.',
          ),
          right: _buildListCard(
            title: 'Avoid Ingredients',
            items: avoidIngredients,
            sectionIcon: Icons.gpp_bad_outlined,
            itemIcon: Icons.shield_outlined,
            color: _danger,
            emptyState: 'No specific avoid ingredients listed.',
          ),
        ),
        const SizedBox(height: 14),

        _buildTwoColumn(
          left: _buildListCard(
            title: 'Routine (AM)',
            items: routineAM,
            sectionIcon: Icons.wb_sunny_outlined,
            itemIcon: Icons.brightness_5_outlined,
            color: _warning,
            emptyState: 'No AM routine provided.',
          ),
          right: _buildListCard(
            title: 'Routine (PM)',
            items: routinePM,
            sectionIcon: Icons.bedtime_outlined,
            itemIcon: Icons.nights_stay_outlined,
            color: _brandDark,
            emptyState: 'No PM routine provided.',
          ),
        ),
        const SizedBox(height: 16),

        if (nextSteps.isNotEmpty) ...[
          _buildListCard(
            title: 'Next Steps',
            items: nextSteps,
            sectionIcon: Icons.checklist_outlined,
            itemIcon: Icons.chevron_right,
            color: _brandDark,
            emptyState: 'No next steps provided.',
          ),
          const SizedBox(height: 14),
        ],

        if (limitations.isNotEmpty) ...[
          _buildListCard(
            title: 'Limitations',
            items: limitations,
            sectionIcon: Icons.rule_outlined,
            itemIcon: Icons.info_outline,
            color: _warning,
            emptyState: 'No limitations provided.',
          ),
          const SizedBox(height: 14),
        ],

        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: _warning.withValues(alpha: 0.10),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: _warning.withValues(alpha: 0.32)),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.info_outline, color: _warning),
              const SizedBox(width: 9),
              Expanded(
                child: Text(
                  note,
                  style: TextStyle(
                    fontWeight: FontWeight.w500,
                    color: context.isDarkMode ? Colors.orangeAccent : _warning,
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 24),

        SizedBox(
          width: double.infinity,
          height: 52,
          child: OutlinedButton.icon(
            onPressed: _resetAll,
            icon: const Icon(Icons.refresh),
            label: const Text('Analyze Another Photo'),
            style: OutlinedButton.styleFrom(
              foregroundColor: _brandDark,
              side: BorderSide(color: _brand.withValues(alpha: 0.42)),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(30),
              ),
            ),
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Skin Care Assistant'),
        backgroundColor: context.clrSurface,
        surfaceTintColor: Colors.transparent,
        shadowColor: Colors.black.withValues(alpha: 0.08),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(18, 14, 18, 22),
          child: _analysisResult == null
              ? _buildInputView()
              : _buildResultView(),
        ),
      ),
    );
  }
}
