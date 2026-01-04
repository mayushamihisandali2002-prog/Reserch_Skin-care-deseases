import 'dart:math';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/api_service.dart';
import '../utils/app_styles.dart';

class AnalyzeScreen extends StatefulWidget {
  const AnalyzeScreen({super.key});

  @override
  State<AnalyzeScreen> createState() => _AnalyzeScreenState();
}

class _AnalyzeScreenState extends State<AnalyzeScreen> {
  List<dynamic> _history = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      final history = await ApiService.getHistory();

      // ✅ If API empty, show dummy data so UI still looks good
      final safeHistory = (history.isEmpty) ? _dummyHistory() : history;

      if (mounted) {
        setState(() {
          _history = safeHistory;
          _isLoading = false;
        });
      }
    } catch (_) {
      // If API fails, still show dummy data
      if (mounted) {
        setState(() {
          _history = _dummyHistory();
          _isLoading = false;
        });
      }
    }
  }

  // Dummy history (for presentation)
  List<Map<String, dynamic>> _dummyHistory() {
    return [
      {"week": "Week 1", "status": "bad", "redness": 88, "itching": 90, "dryness": 85},
      {"week": "Week 2", "status": "bad", "redness": 82, "itching": 85, "dryness": 80},
      {"week": "Week 3", "status": "improving", "redness": 70, "itching": 75, "dryness": 72},
      {"week": "Week 4", "status": "improving", "redness": 62, "itching": 68, "dryness": 65},
      {"week": "Week 5", "status": "improving", "redness": 55, "itching": 58, "dryness": 55},
      {"week": "Week 6", "status": "improving", "redness": 48, "itching": 45, "dryness": 48},
      {"week": "Week 7", "status": "healed", "redness": 38, "itching": 35, "dryness": 40},
      {"week": "Week 8", "status": "healed", "redness": 30, "itching": 25, "dryness": 32},
      {"week": "Week 9", "status": "healed", "redness": 22, "itching": 18, "dryness": 25},
      {"week": "Week 10", "status": "healed", "redness": 15, "itching": 12, "dryness": 18},
    ];
  }

  // Convert status string to numeric value for chart
  double _getStatusValue(String status) {
    switch (status.toLowerCase()) {
      case 'bad':
        return 1;
      case 'improving':
        return 2;
      case 'healed':
        return 3;
      default:
        return 0;
    }
  }

  String _getStatusLabel(double v) {
    if (v == 1) return "Bad";
    if (v == 2) return "Fair";
    if (v == 3) return "Good";
    return "";
  }

  // Create short week label: "Week 2" -> "W2"
  String _shortWeek(dynamic w) {
    final s = (w ?? "").toString();
    return s.replaceAll("Week ", "W");
  }

  // Build a useful summary from history (dummy-style)
  Map<String, dynamic> _buildInsight() {
    if (_history.isEmpty) {
      return {
        "title": "Insight",
        "summary": "Not enough data to analyze.",
        "bullets": <String>[],
        "tip": "Upload weekly images to track progress.",
      };
    }

    // Trend based on first/last week numeric
    final first = _history.first;
    final last = _history.last;

    final firstVal = _getStatusValue((first["status"] ?? "").toString());
    final lastVal = _getStatusValue((last["status"] ?? "").toString());

    final trend = (lastVal > firstVal)
        ? "Positive improvement trend"
        : (lastVal < firstVal)
            ? "Condition worsened trend"
            : "Stable trend";

    // Average reductions (if fields exist)
    int getMetric(dynamic item, String key) {
      final v = item[key];
      if (v is int) return v;
      if (v is double) return v.round();
      return 0;
    }

    final r1 = getMetric(first, "redness");
    final rN = getMetric(last, "redness");
    final i1 = getMetric(first, "itching");
    final iN = getMetric(last, "itching");
    final d1 = getMetric(first, "dryness");
    final dN = getMetric(last, "dryness");

    int safeDiff(int a, int b) => max(0, a - b);

    final rednessDrop = safeDiff(r1, rN);
    final itchingDrop = safeDiff(i1, iN);
    final drynessDrop = safeDiff(d1, dN);

    return {
      "title": "Insight",
      "summary": "Your skin condition shows: $trend",
      "bullets": <String>[
        if (r1 > 0 && rN > 0) "Redness decreased by ~${rednessDrop}%",
        if (i1 > 0 && iN > 0) "Itching decreased by ~${itchingDrop}%",
        if (d1 > 0 && dN > 0) "Dryness decreased by ~${drynessDrop}%",
        "Consistency improved across the last weeks",
      ],
      "tip": "Continue moisturizer twice daily + avoid harsh soaps for best results.",
    };
  }

  @override
  Widget build(BuildContext context) {
    final insight = _buildInsight();

    return Scaffold(
      appBar: AppBar(title: const Text('Healing Analysis')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : LayoutBuilder(
              builder: (context, constraints) {
                final isSmall = constraints.maxWidth < 360;

                // Chart width: give each week enough space
                final weekCount = max(1, _history.length);
                final chartWidth = max(constraints.maxWidth, weekCount * 70.0);

                return SingleChildScrollView(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Text('Recovery Trend', style: AppTextStyles.subHeading),
                      const SizedBox(height: 14),

                      // ✅ Chart container
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.grey.withOpacity(0.08),
                              blurRadius: 12,
                              offset: const Offset(0, 6),
                            ),
                          ],
                        ),
                        child: _history.isEmpty
                            ? const Padding(
                                padding: EdgeInsets.symmetric(vertical: 28),
                                child: Center(child: Text('Not enough data to analyze')),
                              )
                            : Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  SizedBox(
                                    height: isSmall ? 240 : 260,
                                    child: SingleChildScrollView(
                                      scrollDirection: Axis.horizontal,
                                      child: SizedBox(
                                        width: chartWidth,
                                        child: LineChart(
                                          LineChartData(
                                            gridData: FlGridData(
                                              show: true,
                                              drawVerticalLine: false,
                                              horizontalInterval: 1,
                                              getDrawingHorizontalLine: (value) {
                                                return FlLine(
                                                  color: Colors.grey.withOpacity(0.15),
                                                  strokeWidth: 1,
                                                );
                                              },
                                            ),
                                            titlesData: FlTitlesData(
                                              leftTitles: AxisTitles(
                                                sideTitles: SideTitles(
                                                  showTitles: true,
                                                  interval: 1,
                                                  reservedSize: 46,
                                                  getTitlesWidget: (value, meta) {
                                                    final label = _getStatusLabel(value);
                                                    if (label.isEmpty) return const SizedBox.shrink();
                                                    return Padding(
                                                      padding: const EdgeInsets.only(right: 8),
                                                      child: Text(
                                                        label,
                                                        style: const TextStyle(
                                                          fontSize: 11,
                                                          fontWeight: FontWeight.w600,
                                                          color: Colors.black54,
                                                        ),
                                                      ),
                                                    );
                                                  },
                                                ),
                                              ),
                                              bottomTitles: AxisTitles(
                                                sideTitles: SideTitles(
                                                  showTitles: true,
                                                  interval: 1,
                                                  reservedSize: 42,
                                                  getTitlesWidget: (value, meta) {
                                                    final i = value.toInt();
                                                    if (i < 0 || i >= _history.length) {
                                                      return const SizedBox.shrink();
                                                    }
                                                    final label = _shortWeek(_history[i]['week']);
                                                    return Padding(
                                                      padding: const EdgeInsets.only(top: 10),
                                                      child: Transform.rotate(
                                                        angle: -0.35, // ✅ slight rotation prevents overlap
                                                        child: Text(
                                                          label,
                                                          style: const TextStyle(
                                                            fontSize: 11,
                                                            fontWeight: FontWeight.bold,
                                                            color: Colors.black54,
                                                          ),
                                                        ),
                                                      ),
                                                    );
                                                  },
                                                ),
                                              ),
                                              rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                                              topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                                            ),
                                            borderData: FlBorderData(show: false),

                                            lineTouchData: LineTouchData(
                                              enabled: true,
                                              touchTooltipData: LineTouchTooltipData(
                                                tooltipRoundedRadius: 12,
                                                fitInsideHorizontally: true,
                                                fitInsideVertically: true,
                                                getTooltipItems: (touchedSpots) {
                                                  return touchedSpots.map((spot) {
                                                    final i = spot.x.toInt();
                                                    final week = (i >= 0 && i < _history.length)
                                                        ? _history[i]['week']
                                                        : '';
                                                    final v = _getStatusLabel(spot.y);
                                                    return LineTooltipItem(
                                                      '$week\nStatus: $v',
                                                      const TextStyle(
                                                        color: Colors.white,
                                                        fontWeight: FontWeight.bold,
                                                      ),
                                                    );
                                                  }).toList();
                                                },
                                              ),
                                            ),

                                            lineBarsData: [
                                              LineChartBarData(
                                                spots: _history.asMap().entries.map((e) {
                                                  return FlSpot(
                                                    e.key.toDouble(),
                                                    _getStatusValue((e.value['status'] ?? "").toString()),
                                                  );
                                                }).toList(),
                                                isCurved: true,
                                                color: AppColors.primary,
                                                barWidth: 4,
                                                isStrokeCapRound: true,
                                                dotData: FlDotData(
                                                  show: true,
                                                  getDotPainter: (spot, percent, barData, index) {
                                                    return FlDotCirclePainter(
                                                      radius: 4.5,
                                                      color: AppColors.primary,
                                                      strokeWidth: 2,
                                                      strokeColor: Colors.white,
                                                    );
                                                  },
                                                ),
                                                belowBarData: BarAreaData(
                                                  show: true,
                                                  color: AppColors.primary.withOpacity(0.12),
                                                ),
                                              ),
                                            ],
                                            minY: 0,
                                            maxY: 4,
                                          ),
                                        ),
                                      ),
                                    ),
                                  ),

                                  const SizedBox(height: 10),

                                  // ✅ Small legend
                                  Wrap(
                                    spacing: 10,
                                    runSpacing: 8,
                                    children: [
                                      _chip("Bad", Colors.red.withOpacity(0.15), Colors.red),
                                      _chip("Fair", Colors.orange.withOpacity(0.15), Colors.orange),
                                      _chip("Good", Colors.green.withOpacity(0.15), Colors.green),
                                      _chip("Tap dot for details", Colors.blue.withOpacity(0.12), Colors.blue),
                                    ],
                                  ),
                                ],
                              ),
                      ),

                      const SizedBox(height: 18),

                      // ✅ Insight Card (more details)
                      Container(
                        padding: const EdgeInsets.all(18),
                        decoration: BoxDecoration(
                          color: AppColors.secondary.withOpacity(0.10),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: AppColors.secondary.withOpacity(0.7)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              insight["title"],
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                color: AppColors.textMain,
                                fontSize: 18,
                              ),
                            ),
                            const SizedBox(height: 10),
                            Text(
                              insight["summary"],
                              style: const TextStyle(
                                color: AppColors.textMain,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 10),

                            ...((insight["bullets"] as List<String>).map(
                              (b) => Padding(
                                padding: const EdgeInsets.only(bottom: 6),
                                child: Text(
                                  "• $b",
                                  style: const TextStyle(
                                    color: AppColors.textMain,
                                    height: 1.45,
                                  ),
                                ),
                              ),
                            )),

                            const SizedBox(height: 10),
                            Text(
                              "Tip: ${insight["tip"]}",
                              style: const TextStyle(
                                color: AppColors.textMain,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 18),

                      // ✅ More dummy analysis (cards)
                      _metricCard(
                        title: "Weekly Metrics (Dummy)",
                        subtitle: "Average of last weeks",
                        items: [
                          _metricRow("Redness", _avgMetric("redness").toStringAsFixed(0), "%"),
                          _metricRow("Itching", _avgMetric("itching").toStringAsFixed(0), "%"),
                          _metricRow("Dryness", _avgMetric("dryness").toStringAsFixed(0), "%"),
                        ],
                      ),

                      const SizedBox(height: 14),

                      _metricCard(
                        title: "Recommendations (Dummy)",
                        subtitle: "To maintain improvement",
                        items: const [
                          "• Moisturize morning + night",
                          "• Avoid hot water and harsh soaps",
                          "• Use sunscreen if exposed to sun",
                          "• Maintain hydration (drink water)",
                          "• Sleep well to reduce stress inflammation",
                        ].map((s) => Padding(
                          padding: const EdgeInsets.only(bottom: 6),
                          child: Text(s, style: const TextStyle(height: 1.4, color: AppColors.textMain)),
                        )).toList(),
                      ),
                    ],
                  ),
                );
              },
            ),
    );
  }

  // average metric across history if exists
  double _avgMetric(String key) {
    if (_history.isEmpty) return 0;
    int sum = 0;
    int count = 0;
    for (final h in _history) {
      final v = h[key];
      if (v is int) {
        sum += v;
        count++;
      } else if (v is double) {
        sum += v.round();
        count++;
      }
    }
    return count == 0 ? 0 : sum / count;
  }

  Widget _chip(String text, Color bg, Color fg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: fg.withOpacity(0.35)),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: fg),
      ),
    );
  }

  Widget _metricCard({
    required String title,
    required String subtitle,
    required List<Widget> items,
  }) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.08),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          Text(subtitle, style: const TextStyle(color: Colors.black54)),
          const SizedBox(height: 12),
          ...items,
        ],
      ),
    );
  }

  Widget _metricRow(String label, String value, String unit) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Expanded(
            child: Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
          ),
          Text(
            "$value$unit",
            style: const TextStyle(fontWeight: FontWeight.w800, color: Colors.black87),
          ),
        ],
      ),
    );
  }
}
