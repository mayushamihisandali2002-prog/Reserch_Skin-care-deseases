import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:image_picker/image_picker.dart';
import 'healing_analysis_screen.dart';
import 'dart:io';
import '../services/api_service.dart';
import '../utils/app_styles.dart';

class ProgressScreen extends StatefulWidget {
  const ProgressScreen({super.key});

  @override
  State<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends State<ProgressScreen> {
  List<dynamic> _history = [];
  bool _isLoading = true;
  bool _isUploading = false;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final history = await ApiService.getHistory();
    if (mounted) {
      setState(() {
        _history = history;
        _isLoading = false;
      });
    }
  }

  Future<void> _addCheckIn() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);

    if (pickedFile != null) {
      setState(() {
        _isUploading = true;
      });

      try {
        final result = await ApiService.addProgress(pickedFile.path);
        
        if (!mounted) return;

        // Show result dialog
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Analysis Complete'),
            content: Text(result['analysis'] ?? 'Weekly check-in logged.'),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                  _loadHistory(); // Refresh list
                },
                child: const Text('OK'),
              ),
            ],
          ),
        );

      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e')),
          );
        }
      } finally {
        if (mounted) {
          setState(() {
            _isUploading = false;
          });
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Weekly Progress')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _isUploading ? null : _addCheckIn,
        label: _isUploading 
            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) 
            : const Text('Add Weekly Check-in'),
        icon: _isUploading ? null : const Icon(Icons.add_a_photo),
        backgroundColor: AppColors.primary,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _history.isEmpty
              ? const Center(child: Text('No progress logs yet.\nStart by adding your first check-in!', textAlign: TextAlign.center))
              : ListView( // Changed to ListView to include chart
                  padding: const EdgeInsets.all(16),
                  children: [
                    // Trend Chart
                    const Text('Healing Trend', style: AppTextStyles.subHeading),
                    const SizedBox(height: 16),
                    _buildTrendChart(),
                    const SizedBox(height: 24),

                    const Text('History', style: AppTextStyles.subHeading),
                    const SizedBox(height: 16),
                    
                    ...List.generate(_history.length, (index) {
                      // Show newest first
                      final item = _history[_history.length - 1 - index];
                      return GestureDetector(
                        onTap: () {
                          Navigator.of(context).push(
                             MaterialPageRoute(builder: (context) => HealingAnalysisScreen(data: item)),
                          );
                        },
                        child: Card(
                          margin: const EdgeInsets.only(bottom: 16),
                          elevation: 2,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                          child: Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                // Thumbnail
                                Container(
                                  width: 80,
                                  height: 80,
                                  decoration: BoxDecoration(
                                    color: Colors.grey[200],
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: const Icon(Icons.image, color: Colors.grey),
                                ),
                                const SizedBox(width: 16),
                                
                                // Info
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(item['week'] ?? 'Week ?', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                            decoration: BoxDecoration(
                                              color: AppColors.success.withOpacity(0.1),
                                              borderRadius: BorderRadius.circular(20),
                                            ),
                                            child: Text(item['status'] ?? 'Unknown', style: const TextStyle(color: AppColors.success, fontSize: 12, fontWeight: FontWeight.bold)),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 8),
                                      Text(
                                        'Score: ${item['score']}%',
                                        style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(item['date'] ?? '', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    }),
                  ],
                ),
    );
  }

  Widget _buildTrendChart() {
    return Container(
      height: 200,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(color: Colors.grey.withOpacity(0.1), blurRadius: 10, offset: const Offset(0, 5)),
        ],
      ),
      child: LineChart(
        LineChartData(
          gridData: FlGridData(show: false),
          titlesData: FlTitlesData(
            leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 30)),
            bottomTitles: AxisTitles(
               sideTitles: SideTitles(
                 showTitles: true,
                 getTitlesWidget: (value, meta) {
                   int index = value.toInt();
                   if (index >= 0 && index < _history.length) {
                     return Text('W${index+1}', style: const TextStyle(fontSize: 10));
                   }
                   return const SizedBox();
                 },
               ),
            ),
            rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
            topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          ),
          borderData: FlBorderData(show: false),
          lineBarsData: [
            LineChartBarData(
              spots: _history.asMap().entries.map((e) {
                return FlSpot(e.key.toDouble(), (e.value['score'] ?? 0).toDouble());
              }).toList(),
              isCurved: true,
              color: AppColors.primary,
              barWidth: 3,
              dotData: FlDotData(show: true),
              belowBarData: BarAreaData(show: true, color: AppColors.primary.withOpacity(0.1)),
            ),
          ],
        ),
      ),
    );
  }
}
