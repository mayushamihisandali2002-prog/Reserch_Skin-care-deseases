import 'package:app/services/supabase_service.dart';
import 'package:app/utils/app_styles.dart';
import 'package:flutter/material.dart';

class JourneySetupScreen extends StatefulWidget {
  const JourneySetupScreen({super.key});

  @override
  State<JourneySetupScreen> createState() => _JourneySetupScreenState();
}

class _JourneySetupScreenState extends State<JourneySetupScreen> {
  final _titleController = TextEditingController();
  final _locationController = TextEditingController();
  String _selectedPart = 'Face';
  String _selectedFrequency = 'weekly';
  bool _isLoading = false;

  final List<String> _bodyParts = ['Face', 'Neck', 'Arm', 'Leg', 'Hand', 'Foot', 'Back', 'Chest', 'Scalp'];
  final List<String> _frequencies = ['daily', 'weekly'];

  Future<void> _startJourney() async {
    if (_titleController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Please enter a title')));
      return;
    }

    setState(() => _isLoading = true);
    try {
      await SupabaseService.startJourney(
        title: _titleController.text.trim(),
        bodyPart: _selectedPart,
        frequency: _selectedFrequency,
      );
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('New Tracking Journey', style: TextStyle(color: context.clrTextMain, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: IconThemeData(color: context.clrTextMain),
      ),
      extendBodyBehindAppBar: true,
      body: Container(
        decoration: BoxDecoration(gradient: AppGradients.page(context)),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'What are we tracking?',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: context.clrTextMain),
                ),
                const SizedBox(height: 8),
                Text(
                  'Create a session to track progress and receive warnings if photos don\'t match.',
                  style: TextStyle(color: context.clrTextSec),
                ),
                const SizedBox(height: 32),
                
                _buildFieldLabel('Journey Title'),
                _buildTextField(
                  controller: _titleController,
                  hint: 'e.g., Left Cheek Acne, Arm Rash',
                  icon: Icons.title_rounded,
                ),
                const SizedBox(height: 24),

                _buildFieldLabel('Body Part'),
                _buildDropdown(
                  value: _selectedPart,
                  items: _bodyParts,
                  icon: Icons.accessibility_new_rounded,
                  onChanged: (val) => setState(() => _selectedPart = val!),
                ),
                const SizedBox(height: 24),

                _buildFieldLabel('Tracking Frequency'),
                Row(
                  children: _frequencies.map((f) {
                    final isSelected = _selectedFrequency == f;
                    return Expanded(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 4.0),
                        child: InkWell(
                          onTap: () => setState(() => _selectedFrequency = f),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 200),
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            decoration: isSelected
                                ? AppDecor.softCard(context, color: AppColors.primary, showBorder: false)
                                : AppDecor.softCard(context, color: Colors.white),
                            child: Center(
                              child: Text(
                                f.toUpperCase(),
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: isSelected ? Colors.white : context.clrTextMain,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 40),

                SizedBox(
                  width: double.infinity,
                  height: 58,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _startJourney,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    ),
                    child: _isLoading
                        ? const CircularProgressIndicator(color: Colors.white)
                        : const Text('START JOURNEY', style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1.2)),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFieldLabel(String label) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Text(
        label,
        style: TextStyle(fontWeight: FontWeight.bold, color: context.clrTextMain, fontSize: 16),
      ),
    );
  }

  Widget _buildTextField({required TextEditingController controller, required String hint, required IconData icon}) {
    return Container(
      decoration: AppDecor.softCard(context, color: Colors.white),
      child: TextField(
        controller: controller,
        decoration: InputDecoration(
          hintText: hint,
          prefixIcon: Icon(icon, color: AppColors.primary),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.all(16),
        ),
      ),
    );
  }

  Widget _buildDropdown({required String value, required List<String> items, required IconData icon, required ValueChanged<String?> onChanged}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: AppDecor.softCard(context, color: Colors.white),
      child: DropdownButtonFormField<String>(
        value: value,
        items: items.map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
        onChanged: onChanged,
        decoration: InputDecoration(
          prefixIcon: Icon(icon, color: AppColors.primary),
          border: InputBorder.none,
        ),
      ),
    );
  }
}
