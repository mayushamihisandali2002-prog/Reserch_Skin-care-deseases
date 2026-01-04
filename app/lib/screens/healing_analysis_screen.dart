import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../utils/app_styles.dart';

class HealingAnalysisScreen extends StatelessWidget {
  final Map<String, dynamic> data;

  const HealingAnalysisScreen({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final metrics = data['metrics'] as Map<String, dynamic>? ?? {};

    return Scaffold(
      appBar: AppBar(title: Text(data['week'] ?? 'Analysis Detail')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [AppColors.primary, AppColors.secondary]),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                children: [
                  Text('Overall Score', style: const TextStyle(color: Colors.white, fontSize: 16)),
                  const SizedBox(height: 8),
                  Text('${data['score']}%', style: const TextStyle(color: Colors.white, fontSize: 48, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(color: Colors.white.withOpacity(0.2), borderRadius: BorderRadius.circular(20)),
                    child: Text(data['status'] ?? 'Unknown', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 30),

            // Radar Chart Section
            const Text('Symptom Breakdown', style: AppTextStyles.subHeading),
            const SizedBox(height: 20),
            _buildRadarChart(metrics),
            const SizedBox(height: 30),

            // Detailed Metrics Grid
            const Text('Detailed Metrics', style: AppTextStyles.subHeading),
            const SizedBox(height: 16),
            _buildMetricsGrid(metrics),
            
            const SizedBox(height: 30),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: Colors.blue[50], borderRadius: BorderRadius.circular(16)),
              child: Row(
                children: [
                   const Icon(Icons.info, color: Colors.blue),
                   const SizedBox(width: 12),
                   const Expanded(child: Text('Lower values are better for Redness, Inflammation, and Scaling. Higher is better for Texture/Healing.')),
                ],
              ),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildRadarChart(Map<String, dynamic> metrics) {
    final values = [
      (metrics['redness'] ?? 0).toDouble(),
      (metrics['inflammation'] ?? 0).toDouble(),
      (metrics['scaling'] ?? 0).toDouble(),
      (metrics['texture'] ?? 0).toDouble(),
    ];
    
    // Normalize for chart (texture is "good" high, others "bad" high - simplify for now by plotting raw)
    
    return SizedBox(
      height: 300,
      child: RadarChart(
        RadarChartData(
          ticksTextStyle: const TextStyle(color: Colors.transparent),
          gridBorderData: BorderSide(color: Colors.grey[300]!),
          titlePositionPercentageOffset: 0.2,
          getTitle: (index, angle) {
            const titles = ['Redness', 'Inflammation', 'Scaling', 'Texture'];
            return RadarChartTitle(text: titles[index % titles.length]);
          },
          dataSets: [
            RadarDataSet(
              fillColor: AppColors.primary.withOpacity(0.4),
              borderColor: AppColors.primary,
              entryRadius: 3,
              dataEntries: values.map((e) => RadarEntry(value: e)).toList(),
              borderWidth: 2,
            )
          ],
          radarBackgroundColor: Colors.transparent,
          borderData: FlBorderData(show: false),
          radarBorderData: const BorderSide(color: Colors.transparent),
          tickBorderData: const BorderSide(color: Colors.transparent),
          radarShape: RadarShape.polygon,
        ),
      ),
    );
  }

  Widget _buildMetricsGrid(Map<String, dynamic> metrics) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 16,
      mainAxisSpacing: 16,
      childAspectRatio: 1.5,
      children: metrics.entries.map((e) {
        Color color = AppColors.primary;
        if (e.key == 'redness' || e.key == 'inflammation') color = Colors.red;
        if (e.key == 'texture') color = Colors.green;
        
        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [BoxShadow(color: Colors.grey.withOpacity(0.1), blurRadius: 4)],
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                e.key.toUpperCase(), 
                style: const TextStyle(color: Colors.grey, fontSize: 12, fontWeight: FontWeight.bold)
              ),
              const SizedBox(height: 8),
              Text(
                '${e.value}', 
                style: TextStyle(color: color, fontSize: 24, fontWeight: FontWeight.bold)
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}
