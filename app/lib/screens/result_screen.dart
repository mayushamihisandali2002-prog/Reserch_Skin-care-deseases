import 'package:flutter/material.dart';
import '../utils/app_styles.dart';

class ResultScreen extends StatelessWidget {
  final Map<String, dynamic> data;

  const ResultScreen({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    // Extract data safe
    final String prediction = data['prediction'] ?? 'Unknown';
    final double confidence = (data['confidence'] ?? 0.0) * 100;
    final List symptoms = data['symptoms'] ?? [];
    final List triggers = data['triggers'] ?? [];
    final Map routine = data['routine'] ?? {};
    final List warnings = data['warnings'] ?? [];

    return Scaffold(
      appBar: AppBar(title: const Text('Analysis Result')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Prediction Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                children: [
                  Text(
                    prediction,
                    style: AppTextStyles.heading.copyWith(color: Colors.white, fontSize: 32),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Confidence: ${confidence.toStringAsFixed(1)}%',
                    style: AppTextStyles.body.copyWith(color: Colors.white70),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Symptoms
            const Text('Common Symptoms', style: AppTextStyles.subHeading),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: symptoms.map((e) => Chip(
                label: Text(e.toString()),
                backgroundColor: AppColors.secondary.withOpacity(0.1),
                labelStyle: const TextStyle(color: AppColors.textMain),
              )).toList(),
            ),
            const SizedBox(height: 24),

            // Routine
            const Text('Recommended Routine', style: AppTextStyles.subHeading),
            const SizedBox(height: 12),
            _buildRoutineItem('Morning', routine['morning'] ?? 'N/A', Icons.wb_sunny),
            _buildRoutineItem('Night', routine['night'] ?? 'N/A', Icons.nightlight_round),
            _buildRoutineItem('Treatment', routine['treatment'] ?? 'N/A', Icons.medical_services),

            // Warnings
            if (warnings.isNotEmpty) ...[
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.error.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.error),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.warning_amber_rounded, color: AppColors.error),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        warnings.join('\n'),
                        style: const TextStyle(color: AppColors.error, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildRoutineItem(String title, String desc, IconData icon) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(8),
              boxShadow: [
                BoxShadow(color: Colors.grey.withOpacity(0.1), blurRadius: 4, offset: const Offset(0, 2)),
              ],
            ),
            child: Icon(icon, color: AppColors.primary),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
                Text(desc, style: AppTextStyles.body),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
