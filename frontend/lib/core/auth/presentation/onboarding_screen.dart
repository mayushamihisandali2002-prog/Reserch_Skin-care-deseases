import 'package:app/services/supabase_service.dart';
import 'package:app/utils/app_styles.dart';
import 'package:flutter/material.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  int _currentStep = 0;
  bool _isLoading = false;

  // Form controllers
  final _nameController = TextEditingController();
  String _selectedGender = 'prefer_not_to_say';
  String _selectedSkinType = 'normal';
  final _allergiesController = TextEditingController();
  DateTime? _dob;

  final List<String> _skinTypes = ['normal', 'dry', 'oily', 'combination', 'sensitive'];
  final List<String> _genders = ['male', 'female', 'other', 'prefer_not_to_say'];

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _allergiesController.dispose();
    super.dispose();
  }

  Future<void> _loadProfile() async {
    final profile = await SupabaseService.getProfile();
    if (!mounted) return;

    setState(() {
      _nameController.text = (profile?['full_name'] ??
              SupabaseService.currentUser?.userMetadata?['full_name'] ??
              '')
          .toString();
      _selectedGender = profile?['gender'] ?? 'prefer_not_to_say';
      _selectedSkinType = profile?['skin_type'] ?? 'normal';
      _allergiesController.text = ((profile?['allergies'] as List?) ?? const [])
          .map((e) => '$e')
          .join(', ');
      if (profile?['date_of_birth'] != null) {
        _dob = DateTime.tryParse(profile!['date_of_birth'].toString());
      }
    });
  }

  Future<void> _saveAndContinue() async {
    if (_currentStep == 0 && _nameController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter your full name.')),
      );
      return;
    }

    if (_currentStep < 2) {
      setState(() => _currentStep++);
      return;
    }

    setState(() => _isLoading = true);
    try {
      final allergies = _allergiesController.text
          .split(',')
          .map((e) => e.trim())
          .where((e) => e.isNotEmpty)
          .toList();

      await SupabaseService.updateProfile(
        fullName: _nameController.text.trim(),
        gender: _selectedGender,
        skinType: _selectedSkinType,
        dateOfBirth: _dob,
        allergies: allergies,
      );

      if (!mounted) return;
      Navigator.of(context).pushNamedAndRemoveUntil(
        '/home',
        (route) => false,
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(gradient: AppGradients.page(context)),
        child: SafeArea(
          child: Column(
            children: [
              _buildHeader(),
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      if (_currentStep == 0) _buildPersonalInfoStep(),
                      if (_currentStep == 1) _buildSkinTypeStep(),
                      if (_currentStep == 2) _buildAllergiesStep(),
                      const SizedBox(height: 32),
                    ],
                  ),
                ),
              ),
              _buildBottomNav(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          LinearProgressIndicator(
            value: (_currentStep + 1) / 3,
            backgroundColor: Colors.white24,
            valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primary),
            minHeight: 8,
            borderRadius: BorderRadius.circular(4),
          ),
          const SizedBox(height: 24),
          Text(
            _getStepTitle(),
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.w900,
              color: context.clrTextMain,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            _getStepSubtitle(),
            style: TextStyle(
              fontSize: 16,
              color: context.clrTextSec,
            ),
          ),
        ],
      ),
    );
  }

  String _getStepTitle() {
    switch (_currentStep) {
      case 0: return 'Basic Info';
      case 1: return 'Your Skin Type';
      case 2: return 'Any Allergies?';
      default: return '';
    }
  }

  String _getStepSubtitle() {
    switch (_currentStep) {
      case 0: return 'Let\'s get to know you better.';
      case 1: return 'This helps our AI tailor its advice.';
      case 2: return 'Safety first! Tell us about sensitivities.';
      default: return '';
    }
  }

  Widget _buildPersonalInfoStep() {
    return Column(
      children: [
        _buildTextField(
          controller: _nameController,
          label: 'Full Name',
          icon: Icons.person_outline,
        ),
        const SizedBox(height: 20),
        _buildDropdown(
          value: _selectedGender,
          items: _genders,
          label: 'Gender',
          icon: Icons.face_outlined,
          onChanged: (val) => setState(() => _selectedGender = val!),
        ),
        const SizedBox(height: 20),
        InkWell(
          onTap: () async {
            final date = await showDatePicker(
              context: context,
              initialDate: DateTime.now().subtract(const Duration(days: 365 * 25)),
              firstDate: DateTime(1900),
              lastDate: DateTime.now(),
            );
            if (date != null) setState(() => _dob = date);
          },
          child: _buildTextField(
            controller: TextEditingController(
              text: _dob == null ? '' : '${_dob!.day}/${_dob!.month}/${_dob!.year}',
            ),
            label: 'Date of Birth',
            icon: Icons.calendar_today_outlined,
            enabled: false,
          ),
        ),
      ],
    );
  }

  Widget _buildSkinTypeStep() {
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: _skinTypes.map((type) {
        final isSelected = _selectedSkinType == type;
        return InkWell(
          onTap: () => setState(() => _selectedSkinType = type),
          child: Container(
            width: (MediaQuery.of(context).size.width - 60) / 2,
            padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
            decoration: isSelected
                ? AppDecor.softCard(context, color: AppColors.primary, showBorder: false)
                : AppDecor.softCard(context, color: Colors.white, showBorder: true),
            child: Column(
              children: [
                Icon(
                  _getSkinTypeIcon(type),
                  color: isSelected ? Colors.white : AppColors.primary,
                  size: 32,
                ),
                const SizedBox(height: 12),
                Text(
                  type.toUpperCase(),
                  style: TextStyle(
                    fontWeight: FontWeight.w900,
                    fontSize: 15,
                    color: isSelected ? Colors.white : context.clrTextMain,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _getSkinTypeDesc(type),
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 11,
                    color: isSelected ? Colors.white.withValues(alpha: 0.8) : context.clrTextSec,
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  IconData _getSkinTypeIcon(String type) {
    switch (type) {
      case 'oily': return Icons.water_drop_outlined;
      case 'dry': return Icons.cloud_outlined;
      case 'normal': return Icons.face_outlined;
      case 'combination': return Icons.exposure_outlined;
      case 'sensitive': return Icons.favorite_border;
      default: return Icons.help_outline;
    }
  }

  String _getSkinTypeDesc(String type) {
    switch (type) {
      case 'oily': return 'Shiny or greasy face';
      case 'dry': return 'Feels tight or flaky';
      case 'normal': return 'Balanced and healthy';
      case 'combination': return 'Oily nose, dry cheeks';
      case 'sensitive': return 'Stings or turns red easily';
      default: return '';
    }
  }

  Widget _buildAllergiesStep() {
    return Column(
      children: [
        _buildTextField(
          controller: _allergiesController,
          label: 'Allergies (comma separated)',
          hint: 'e.g. Fragrance, Alcohol, Nuts',
          icon: Icons.warning_amber_rounded,
          maxLines: 3,
        ),
        const SizedBox(height: 20),
        Text(
          'Knowing your allergies helps our AI avoid recommending products that might cause irritation.',
          style: TextStyle(color: context.clrTextSec, fontSize: 13, height: 1.5),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    String? hint,
    bool enabled = true,
    int maxLines = 1,
  }) {
    return Container(
      decoration: AppDecor.softCard(context, color: Colors.white),
      child: TextField(
        controller: controller,
        enabled: enabled,
        maxLines: maxLines,
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          prefixIcon: Icon(icon, color: AppColors.primary),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.all(16),
        ),
      ),
    );
  }

  Widget _buildDropdown({
    required String value,
    required List<String> items,
    required String label,
    required IconData icon,
    required ValueChanged<String?> onChanged,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: AppDecor.softCard(context, color: Colors.white),
      child: DropdownButtonFormField<String>(
        initialValue: value,
        items: items.map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
        onChanged: onChanged,
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: Icon(icon, color: AppColors.primary),
          border: InputBorder.none,
        ),
      ),
    );
  }

  Widget _buildBottomNav() {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Row(
        children: [
          if (_currentStep > 0)
            TextButton(
              onPressed: () => setState(() => _currentStep--),
              child: Text('BACK', style: TextStyle(color: context.clrTextSec)),
            ),
          const Spacer(),
          ElevatedButton(
            onPressed: _isLoading ? null : _saveAndContinue,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            ),
            child: _isLoading
                ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : Text(_currentStep == 2 ? 'FINISH' : 'CONTINUE'),
          ),
        ],
      ),
    );
  }
}
