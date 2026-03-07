import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../services/supabase_service.dart';
import '../utils/app_styles.dart';
import '../utils/app_theme.dart';
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
  List<Map<String, dynamic>> _journeys = [];
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
      final journeys = await SupabaseService.getJourneys();
      if (!mounted) return;
      setState(() {
        _history = history;
        _stats = stats;
        _journeys = journeys;
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
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: context.clrSurface,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: context.clrBorder.withValues(alpha: 0.4)),
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: 0.08),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, size: 22, color: color),
          ),
          const SizedBox(height: 16),
          Text(
            value,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: context.clrTextMain,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            title,
            style: AppTextStyles.caption(context).copyWith(
              fontWeight: FontWeight.w600,
              color: context.clrTextSec,
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
      borderRadius: BorderRadius.circular(24),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: AppDecor.softCard(context, radius: 24),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(icon, color: color, size: 26),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: AppTextStyles.bodyStrong(
                      context,
                    ).copyWith(fontSize: 16),
                  ),
                  const SizedBox(height: 4),
                  Text(subtitle, style: AppTextStyles.caption(context)),
                ],
              ),
            ),
            Icon(
              Icons.arrow_forward_ios,
              size: 16,
              color: color.withValues(alpha: 0.5),
            ),
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
      decoration: AppDecor.softCard(context),
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
                FlLine(strokeWidth: 1, color: context.clrBorder.withValues(alpha: 0.1)),
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
                      style: AppTextStyles.caption(
                        context,
                      ).copyWith(fontSize: 11),
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
                    strokeColor: context.clrSurface,
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
      decoration: AppDecor.softCard(context),
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
                    titleStyle: TextStyle(
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
                  Text(
                    displayLabels[index],
                    style: AppTextStyles.caption(context),
                  ),
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
        decoration: AppDecor.softCard(context),
        child: Text(
          'No check-ins yet. Start with your first scan.',
          style: AppTextStyles.body(context),
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
          decoration: AppDecor.softCard(context, color: context.clrSurface),
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
                    Text(week, style: AppTextStyles.bodyStrong(context)),
                    Text(status, style: AppTextStyles.caption(context)),
                  ],
                ),
              ),
              Text(scoreText, style: AppTextStyles.bodyStrong(context)),
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
            onPressed: () {
              final tp = Provider.of<ThemeProvider>(context, listen: false);
              tp.toggleTheme(!tp.isDarkMode);
            },
            icon: Icon(
              context.isDarkMode
                  ? Icons.light_mode_rounded
                  : Icons.dark_mode_rounded,
              color: AppColors.primary,
            ),
            tooltip: 'Toggle Theme',
          ),
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
                    Text(_userName(), style: AppTextStyles.bodyStrong(context)),
                    Text(_userEmail(), style: AppTextStyles.caption(context)),
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
        decoration: BoxDecoration(gradient: AppGradients.page(context)),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _loadData,
                child: ListView(
                  padding: EdgeInsets.zero,
                  children: [
                    Stack(
                      children: [
                        Container(
                          height: 220,
                          decoration: const BoxDecoration(
                            gradient: AppGradients.premium,
                            borderRadius: BorderRadius.only(
                              bottomLeft: Radius.circular(40),
                              bottomRight: Radius.circular(40),
                            ),
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          'Healing Journey',
                                          style: TextStyle(
                                            color: Colors.white.withValues(alpha: 0.7),
                                            fontSize: 12,
                                            fontWeight: FontWeight.w800,
                                            letterSpacing: 1.2,
                                          ),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          'Hello, ${_userName().split(' ').first} ✨',
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 32,
                                            fontWeight: FontWeight.w900,
                                            letterSpacing: -0.5,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  Container(
                                    decoration: BoxDecoration(
                                      color: Colors.white.withValues(alpha: 0.15),
                                      shape: BoxShape.circle,
                                      border: Border.all(color: Colors.white.withValues(alpha: 0.2)),
                                    ),
                                    child: IconButton(
                                      onPressed: _loadData,
                                      icon: const Icon(Icons.refresh_rounded, color: Colors.white, size: 20),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 32),
                              Row(
                                children: [
                                  Expanded(
                                    child: _metricTile(
                                      'Check-ins',
                                      '${_historyCount()}',
                                      Icons.insights_rounded,
                                      AppColors.secondary,
                                    ),
                                  ),
                                  const SizedBox(width: 16),
                                  Expanded(
                                    child: _metricTile(
                                      'Skin Score',
                                      '${_latestScore().toStringAsFixed(0)}%',
                                      Icons.auto_awesome_rounded,
                                      AppColors.success,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Active Journeys',
                            style: AppTextStyles.subHeading(context),
                          ),
                          const SizedBox(height: 16),
                          _buildJourneysSection(),
                          const SizedBox(height: 12),
                          _quickAction(
                            title: 'Smart Diagnosis',
                            subtitle: 'AI multi-modal scan & advice.',
                            icon: Icons.auto_awesome_rounded,
                            color: AppColors.primary,
                            onTap: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => const InstructionScreen(),
                                ),
                              );
                            },
                          ),
                          const SizedBox(height: 12),
                          _quickAction(
                            title: 'Skin Care AI',
                            subtitle: 'Personalized routine guide.',
                            icon: Icons.face_retouching_natural_rounded,
                            color: AppColors.accent,
                            onTap: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => const SkinCareScreen(),
                                ),
                              );
                            },
                          ),
                          const SizedBox(height: 12),
                          _quickAction(
                            title: 'Severity Track',
                            subtitle: 'Face condition deep-scan.',
                            icon: Icons.analytics_rounded,
                            color: AppColors.highlight,
                            onTap: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => const SeverityScreen(),
                                ),
                              );
                            },
                          ),
                          const SizedBox(height: 12),
                          _quickAction(
                            title: 'Healing Progress',
                            subtitle: 'Weekly trends & history.',
                            icon: Icons.history_edu_rounded,
                            color: AppColors.success,
                            onTap: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => const ProgressScreen(),
                                ),
                              );
                            },
                          ),
                          const SizedBox(height: 32),
                          Text(
                            'Skin Health Trend',
                            style: AppTextStyles.subHeading(context),
                          ),
                          const SizedBox(height: 16),
                          _buildScoreChart(),
                          const SizedBox(height: 32),
                          Text(
                            'Symptom Breakdown',
                            style: AppTextStyles.subHeading(context),
                          ),
                          const SizedBox(height: 16),
                          _buildSymptomsChart(),
                          const SizedBox(height: 32),
                          Text(
                            'Recent Activity',
                            style: AppTextStyles.subHeading(context),
                          ),
                          const SizedBox(height: 16),
                          _buildRecentHistory(),
                          const SizedBox(height: 40),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _buildJourneysSection() {
    return Column(
      children: [
        if (_journeys.isEmpty)
          _quickAction(
            title: 'Start New Journey',
            subtitle: 'Track specific skin progress.',
            icon: Icons.add_chart_rounded,
            color: AppColors.success,
            onTap: () async {
              final result = await Navigator.pushNamed(
                context,
                '/journey-setup',
              );
              if (result == true) _loadData();
            },
          )
        else
          SizedBox(
            height: 140,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: _journeys.length + 1,
              itemBuilder: (context, index) {
                if (index == _journeys.length) {
                  return Padding(
                    padding: const EdgeInsets.only(right: 20),
                    child: InkWell(
                      onTap: () async {
                        final result = await Navigator.pushNamed(
                          context,
                          '/journey-setup',
                        );
                        if (result == true) _loadData();
                      },
                      child: Container(
                        width: 140,
                        decoration: AppDecor.softCard(
                          context,
                          color: context.clrSurface.withValues(alpha: 0.2),
                          showBorder: true,
                        ),
                        child: const Icon(
                          Icons.add_circle_outline,
                          color: AppColors.primary,
                          size: 40,
                        ),
                      ),
                    ),
                  );
                }

                final j = _journeys[index];
                return Container(
                  width: 220,
                  margin: const EdgeInsets.only(right: 16),
                  padding: const EdgeInsets.all(16),
                  decoration: AppDecor.softCard(
                    context,
                    color: context.clrSurface,
                    showBorder: true,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 4,
                            ),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              j['body_part'] ?? 'Skin',
                              style: const TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: AppColors.primary,
                              ),
                            ),
                          ),
                          const Icon(
                            Icons.trending_up,
                            color: AppColors.success,
                            size: 16,
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        j['title'] ?? 'Journey',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const Spacer(),
                      Text(
                        'Started: ${j['created_at'].toString().split('T').first}',
                        style: TextStyle(
                          fontSize: 12,
                          color: context.clrTextSec,
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
      ],
    );
  }
}
