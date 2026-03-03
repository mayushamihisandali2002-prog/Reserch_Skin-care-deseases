import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/supabase_service.dart';
import '../utils/app_styles.dart';
import 'instruction_screen.dart';
import 'login_screen.dart';
import 'progress_screen.dart';
import 'severity_screen.dart';
import 'skin_care_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  List<dynamic> _history = [];
  Map<String, dynamic> _stats = {};
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final history = await ApiService.getHistory();
      final stats = await ApiService.getStats();
      if (!mounted) return;
      setState(() {
        _history = history;
        _stats = stats;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _history = [];
        _stats = {};
      });
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  String _userName() {
    final user = SupabaseService.currentUser;
    final name = user?.userMetadata?['full_name'] as String?;
    if (name != null && name.trim().isNotEmpty) {
      return name.trim();
    }
    return 'User';
  }

  String _userEmail() => SupabaseService.currentUser?.email ?? '';

  String _initials() {
    final n = _userName();
    if (n == 'User') {
      final email = _userEmail();
      return email.isEmpty ? 'U' : email[0].toUpperCase();
    }

    final parts = n.split(' ').where((e) => e.isNotEmpty).toList();
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return n[0].toUpperCase();
  }

  Future<void> _logout() async {
    await SupabaseService.signOut();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  Future<void> _showLogoutDialog() async {
    final shouldLogout = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Logout'),
          content: const Text('Are you sure you want to logout?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.error),
              child: const Text('Logout'),
            ),
          ],
        );
      },
    );
    if (shouldLogout == true) {
      await _logout();
    }
  }

  int _historyCount() => _history.length;

  double _latestScore() {
    if (_history.isEmpty) return 0;
    final item = _history.last;
    final score = item is Map ? item['score'] : null;
    if (score is num) return score.toDouble();
    return 0;
  }

  Widget _metricTile(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: AppDecor.softCard(
        color: Colors.white.withValues(alpha: 0.92),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, size: 18, color: color),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: AppTextStyles.caption),
                Text(
                  value,
                  style: AppTextStyles.subHeading.copyWith(fontSize: 16),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _quickAction({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: AppDecor.softCard(),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.16),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: AppTextStyles.bodyStrong),
                  const SizedBox(height: 2),
                  Text(subtitle, style: AppTextStyles.caption),
                ],
              ),
            ),
            const Icon(Icons.chevron_right),
          ],
        ),
      ),
    );
  }

  List<FlSpot> _scoreSpots() {
    final spots = <FlSpot>[];
    for (var i = 0; i < _history.length; i++) {
      final row = _history[i];
      if (row is! Map) continue;
      final v = row['score'];
      if (v is num) {
        spots.add(FlSpot(i.toDouble(), v.toDouble()));
      }
    }
    if (spots.isEmpty) {
      spots.addAll(const [FlSpot(0, 20), FlSpot(1, 35), FlSpot(2, 55)]);
    }
    return spots;
  }

  Widget _buildScoreChart() {
    final spots = _scoreSpots();
    final maxX = spots.last.x;
    return Container(
      height: 250,
      padding: const EdgeInsets.fromLTRB(14, 18, 14, 10),
      decoration: AppDecor.softCard(),
      child: LineChart(
        LineChartData(
          minY: 0,
          maxY: 100,
          minX: 0,
          maxX: maxX < 1 ? 1 : maxX,
          lineTouchData: const LineTouchData(enabled: true),
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            horizontalInterval: 20,
            getDrawingHorizontalLine: (value) =>
                const FlLine(strokeWidth: 1, color: Color(0xFFE8EEF1)),
          ),
          borderData: FlBorderData(show: false),
          titlesData: FlTitlesData(
            rightTitles: const AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
            topTitles: const AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
            leftTitles: const AxisTitles(
              sideTitles: SideTitles(showTitles: true, reservedSize: 34),
            ),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (value, meta) {
                  final index = value.toInt();
                  if (index < 0 || index >= _history.length) {
                    return const SizedBox.shrink();
                  }
                  final row = _history[index];
                  final label =
                      (row is Map ? row['week'] : null)?.toString() ?? '';
                  return Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      label.replaceAll('Week ', 'W'),
                      style: AppTextStyles.caption.copyWith(fontSize: 11),
                    ),
                  );
                },
              ),
            ),
          ),
          lineBarsData: [
            LineChartBarData(
              spots: spots,
              isCurved: true,
              color: AppColors.primary,
              barWidth: 3,
              belowBarData: BarAreaData(
                show: true,
                color: AppColors.primary.withValues(alpha: 0.18),
              ),
              dotData: FlDotData(
                show: true,
                getDotPainter: (spot, percent, barData, index) {
                  return FlDotCirclePainter(
                    radius: 3.4,
                    color: AppColors.primaryDark,
                    strokeColor: Colors.white,
                    strokeWidth: 1.4,
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSymptomsChart() {
    final labels = (_stats['labels'] as List?)?.map((e) => '$e').toList() ?? [];
    final values =
        (_stats['values'] as List?)
            ?.map((e) => (e is num) ? e.toDouble() : 0.0)
            .toList() ??
        [];

    final fallbackLabels = ['Redness', 'Itching', 'Dryness', 'Spots'];
    final fallbackValues = [30.0, 25.0, 22.0, 23.0];

    final displayLabels = labels.isEmpty ? fallbackLabels : labels;
    final displayValues = values.isEmpty ? fallbackValues : values;
    final total = displayValues.fold<double>(0, (sum, v) => sum + v).abs();

    const sectionColors = [
      Color(0xFF1F7A8C),
      Color(0xFFF4A259),
      Color(0xFF6EB5A9),
      Color(0xFFD64550),
      Color(0xFF7A93A0),
    ];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: AppDecor.softCard(),
      child: Column(
        children: [
          SizedBox(
            height: 170,
            child: PieChart(
              PieChartData(
                centerSpaceRadius: 42,
                sectionsSpace: 2,
                sections: List.generate(displayValues.length, (index) {
                  final value = displayValues[index];
                  final percent = total <= 0 ? 0.0 : (value / total) * 100;
                  return PieChartSectionData(
                    value: value,
                    title: '${percent.toStringAsFixed(0)}%',
                    titleStyle: const TextStyle(
                      fontSize: 11,
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                    ),
                    color: sectionColors[index % sectionColors.length],
                    radius: 52,
                  );
                }),
              ),
            ),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: List.generate(displayLabels.length, (index) {
              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 10,
                    height: 10,
                    decoration: BoxDecoration(
                      color: sectionColors[index % sectionColors.length],
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(displayLabels[index], style: AppTextStyles.caption),
                ],
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _buildRecentHistory() {
    if (_history.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: AppDecor.softCard(),
        child: Text(
          'No check-ins yet. Start with your first scan.',
          style: AppTextStyles.body,
        ),
      );
    }

    final items = _history.reversed.take(3).toList();
    return Column(
      children: items.map((item) {
        if (item is! Map) return const SizedBox.shrink();
        final week = (item['week'] ?? 'Week').toString();
        final status = (item['status'] ?? 'Unknown').toString();
        final score = item['score'];
        final scoreText = score is num ? '${score.toStringAsFixed(0)}%' : '-';

        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(14),
          decoration: AppDecor.softCard(color: const Color(0xFFFAFCFD)),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.event_note, color: AppColors.primary),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(week, style: AppTextStyles.bodyStrong),
                    Text(status, style: AppTextStyles.caption),
                  ],
                ),
              ),
              Text(scoreText, style: AppTextStyles.bodyStrong),
            ],
          ),
        );
      }).toList(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            onPressed: _loadData,
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
          ),
          PopupMenuButton<String>(
            icon: CircleAvatar(
              backgroundColor: AppColors.primary.withValues(alpha: 0.12),
              child: Text(
                _initials(),
                style: const TextStyle(
                  fontWeight: FontWeight.w700,
                  color: AppColors.primaryDark,
                ),
              ),
            ),
            onSelected: (value) async {
              if (value == 'logout') {
                await _showLogoutDialog();
              }
            },
            itemBuilder: (context) => [
              PopupMenuItem(
                enabled: false,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_userName(), style: AppTextStyles.bodyStrong),
                    Text(_userEmail(), style: AppTextStyles.caption),
                  ],
                ),
              ),
              const PopupMenuDivider(),
              const PopupMenuItem(
                value: 'logout',
                child: Row(
                  children: [
                    Icon(Icons.logout, color: AppColors.error, size: 18),
                    SizedBox(width: 8),
                    Text('Logout'),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Container(
        decoration: const BoxDecoration(gradient: AppGradients.page),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _loadData,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
                  children: [
                    Container(
                      padding: const EdgeInsets.all(18),
                      decoration: BoxDecoration(
                        gradient: AppGradients.hero,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Welcome, ${_userName().split(' ').first}',
                            style: AppTextStyles.heading.copyWith(
                              color: Colors.white,
                              fontSize: 24,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            'Track your skin journey, run AI analysis, and keep your care plan consistent.',
                            style: AppTextStyles.body.copyWith(
                              color: Colors.white.withValues(alpha: 0.9),
                            ),
                          ),
                          const SizedBox(height: 14),
                          Row(
                            children: [
                              Expanded(
                                child: _metricTile(
                                  'Check-ins',
                                  '${_historyCount()}',
                                  Icons.insights_outlined,
                                  AppColors.secondary,
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: _metricTile(
                                  'Latest Score',
                                  '${_latestScore().toStringAsFixed(0)}%',
                                  Icons.monitor_heart_outlined,
                                  AppColors.accent,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Quick Actions',
                      style: AppTextStyles.subHeading,
                    ),
                    const SizedBox(height: 10),
                    _quickAction(
                      title: 'Disease Diagnosis',
                      subtitle: 'Image + symptoms + voice note workflow.',
                      icon: Icons.camera_alt_outlined,
                      color: AppColors.primary,
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => const InstructionScreen(),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 10),
                    _quickAction(
                      title: 'Skin Care Assistant',
                      subtitle: 'Skin type + personalized routine guidance.',
                      icon: Icons.spa_outlined,
                      color: AppColors.accent,
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => const SkinCareScreen(),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 10),
                    _quickAction(
                      title: 'Face Severity Analysis',
                      subtitle: 'Mild/Moderate/Severe with score and tracking.',
                      icon: Icons.speed_outlined,
                      color: AppColors.warning,
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => const SeverityScreen(),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 10),
                    _quickAction(
                      title: 'Progress History',
                      subtitle: 'Open weekly logs and healing insights.',
                      icon: Icons.timeline_outlined,
                      color: AppColors.success,
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => const ProgressScreen(),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 22),
                    const Text(
                      'Skin Health Trend',
                      style: AppTextStyles.subHeading,
                    ),
                    const SizedBox(height: 10),
                    _buildScoreChart(),
                    const SizedBox(height: 22),
                    const Text(
                      'Symptom Distribution',
                      style: AppTextStyles.subHeading,
                    ),
                    const SizedBox(height: 10),
                    _buildSymptomsChart(),
                    const SizedBox(height: 22),
                    const Text(
                      'Recent Check-ins',
                      style: AppTextStyles.subHeading,
                    ),
                    const SizedBox(height: 10),
                    _buildRecentHistory(),
                  ],
                ),
              ),
      ),
    );
  }
}
