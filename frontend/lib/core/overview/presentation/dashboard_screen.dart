import 'package:fl_chart/fl_chart.dart';
import 'package:app/components/conversational_diagnosis_assistant/presentation/chat_screen.dart';
import 'package:app/components/multimodal_image_audio_diagnosis/presentation/instruction_screen.dart';
import 'package:app/components/severity_assessment_tracking/presentation/progress_screen.dart';
import 'package:app/components/severity_assessment_tracking/presentation/severity_screen.dart';
import 'package:app/components/skin_type_skincare_recommendation/presentation/skin_care_screen.dart';
import 'package:flutter/material.dart';

import 'package:app/core/auth/presentation/login_screen.dart';
import 'package:app/services/api_service.dart';
import 'package:app/services/supabase_service.dart';
import 'package:app/utils/app_styles.dart';

class DashboardScreen extends StatefulWidget {
  final ValueChanged<int>? onSelectTab;

  const DashboardScreen({super.key, this.onSelectTab});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  List<dynamic> _history = [];
  Map<String, dynamic> _stats = {};
  List<Map<String, dynamic>> _journeys = [];
  Map<String, dynamic> _systemStatus = {};
  Map<String, dynamic> _profile = {};
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
      final systemStatus = await ApiService.getSystemStatus();
      final profile = await SupabaseService.getProfile();
      if (!mounted) return;
      setState(() {
        _history = history;
        _stats = stats;
        _journeys = journeys;
        _systemStatus = systemStatus;
        _profile = profile ?? {};
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _history = [];
        _stats = {};
        _journeys = [];
        _systemStatus = {};
        _profile = {};
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

  bool get _isEmbeddedHome => widget.onSelectTab != null;

  void _openTabOrRoute(int tabIndex, Widget fallbackScreen) {
    if (_isEmbeddedHome) {
      widget.onSelectTab!(tabIndex);
      return;
    }

    Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => fallbackScreen));
  }

  double _contentMaxWidth(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    if (width >= 1400) return 1180;
    if (width >= 1024) return 980;
    return width;
  }

  Widget _framed(BuildContext context, Widget child) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: _contentMaxWidth(context)),
        child: child,
      ),
    );
  }

  Widget _metricTile(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 20),
      decoration: BoxDecoration(
        color: context.clrSurface,
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: context.clrBorder.withValues(alpha: 0.5), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: 0.1),
            blurRadius: 30,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(icon, size: 28, color: color),
          ),
          const SizedBox(height: 18),
          Text(
            value,
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.w900,
              color: context.clrTextMain,
              letterSpacing: -0.8,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            title.toUpperCase(),
            style: AppTextStyles.caption(
              context,
            ).copyWith(
              fontWeight: FontWeight.w800, 
              color: context.clrTextSec,
              letterSpacing: 0.5,
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }

  Map<String, dynamic> _validationSummary() {
    final summary = _systemStatus['validation_summary'];
    if (summary is Map) {
      return Map<String, dynamic>.from(summary);
    }
    return {};
  }

  bool get _needsProfileSetup {
    final fullName = (_profile['full_name'] ?? '').toString().trim();
    final skinType = (_profile['skin_type'] ?? '').toString().trim();
    return fullName.isEmpty || skinType.isEmpty;
  }

  Color _statusColor(String? status) {
    final value = (status ?? '').toLowerCase();
    if (value.contains('not_ready') ||
        value.contains('offline') ||
        value.contains('error')) {
      return AppColors.error;
    }
    if (value.contains('warning') || value.contains('partial')) {
      return AppColors.warning;
    }
    if (value.contains('ready') || value.contains('available')) {
      return AppColors.success;
    }
    return context.clrTextSec;
  }

  IconData _statusIcon(String? status) {
    final value = (status ?? '').toLowerCase();
    if (value.contains('not_ready') ||
        value.contains('offline') ||
        value.contains('error')) {
      return Icons.error_rounded;
    }
    if (value.contains('warning') || value.contains('partial')) {
      return Icons.info_rounded;
    }
    if (value.contains('ready') || value.contains('available')) {
      return Icons.check_circle_rounded;
    }
    return Icons.help_outline_rounded;
  }

  String _prettyStatus(String? status) {
    final value = (status ?? 'unknown').trim();
    if (value.isEmpty) return 'unknown';
    return value.replaceAll('_', ' ');
  }

  Widget _statusChip(String label, String? status) {
    final color = _statusColor(status);
    return Container(
      width: 135,
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.15)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(_statusIcon(status), size: 14, color: color),
              const SizedBox(width: 5),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    color: context.clrTextMain,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            _prettyStatus(status),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 10,
              color: color,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProfilePrompt() {
    if (!_needsProfileSetup) return const SizedBox.shrink();

    final fullName = (_profile['full_name'] ?? '').toString().trim();
    final skinType = (_profile['skin_type'] ?? '').toString().trim();
    final missing = <String>[];
    if (fullName.isEmpty) missing.add('name');
    if (skinType.isEmpty) missing.add('skin type');

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: AppDecor.softCard(
        context,
        color: AppColors.primary.withValues(alpha: 0.05),
        borderColor: AppColors.primary.withValues(alpha: 0.16),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(
              Icons.person_outline_rounded,
              color: AppColors.primary,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Complete your profile',
                  style: AppTextStyles.bodyStrong(
                    context,
                  ).copyWith(fontSize: 16),
                ),
                const SizedBox(height: 6),
                Text(
                  'Missing: ${missing.join(' and ')}. Completing this improves skin-type recommendations without blocking the app.',
                  style: AppTextStyles.body(context),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          ElevatedButton(
            onPressed: () async {
              await Navigator.pushNamed(context, '/onboarding');
              if (mounted) {
                _loadData();
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
              ),
              elevation: 0,
            ),
            child: const Text('Set up'),
          ),
        ],
      ),
    );
  }

  Widget _buildReadinessCard() {
    final summary = _validationSummary();
    if (summary.isEmpty) {
      return const SizedBox.shrink();
    }

    final items = <MapEntry<String, String?>>[
      MapEntry('Conversational', summary['text_component']?.toString()),
      MapEntry('Multimodal', summary['fused_component']?.toString()),
      MapEntry('Skin Type', summary['skin_type_component']?.toString()),
      MapEntry('Severity', summary['severity_component']?.toString()),
    ];

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: AppDecor.softCard(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.success.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.monitor_heart_rounded,
                  color: AppColors.success,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Model Readiness',
                      style: AppTextStyles.bodyStrong(
                        context,
                      ).copyWith(fontSize: 16),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Backend status for the four main project components. Standalone image-only diagnosis is disabled and not treated as a primary product path.',
                      style: AppTextStyles.caption(
                        context,
                      ).copyWith(height: 1.3),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: items
                .map((entry) => _statusChip(entry.key, entry.value))
                .toList(),
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
    bool isPrimary = false,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(28),
      child: Container(
        padding: EdgeInsets.all(isPrimary ? 24 : 20),
        decoration: AppDecor.softCard(
          context, 
          radius: 28,
          color: isPrimary ? color : context.clrSurface,
          showBorder: !isPrimary,
        ),
        child: Row(
          children: [
            Container(
              width: isPrimary ? 64 : 52,
              height: isPrimary ? 64 : 52,
              decoration: BoxDecoration(
                color: isPrimary ? Colors.white.withValues(alpha: 0.2) : color.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Icon(
                icon, 
                color: isPrimary ? Colors.white : color, 
                size: isPrimary ? 34 : 28
              ),
            ),
            const SizedBox(width: 20),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: AppTextStyles.bodyStrong(
                      context,
                    ).copyWith(
                      fontSize: isPrimary ? 20 : 17,
                      color: isPrimary ? Colors.white : context.clrTextMain,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle, 
                    style: AppTextStyles.caption(context).copyWith(
                      fontSize: isPrimary ? 13 : 12,
                      color: isPrimary ? Colors.white.withValues(alpha: 0.8) : context.clrTextSec,
                    )
                  ),
                ],
              ),
            ),
            Icon(
              Icons.arrow_forward_ios_rounded,
              size: 20,
              color: isPrimary ? Colors.white.withValues(alpha: 0.8) : color.withValues(alpha: 0.4),
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
            getDrawingHorizontalLine: (value) => FlLine(
              strokeWidth: 1,
              color: context.clrBorder.withValues(alpha: 0.1),
            ),
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

        final scoreNum = score is num ? score.toDouble() : 0.0;
        final scoreColor = scoreNum >= 70 ? AppColors.success : scoreNum >= 40 ? AppColors.warning : AppColors.error;
        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(16),
          decoration: AppDecor.softCard(context, color: context.clrSurface),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.event_note_rounded, color: AppColors.primary, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(week, style: AppTextStyles.bodyStrong(context).copyWith(fontSize: 15)),
                    const SizedBox(height: 2),
                    Text(status, style: AppTextStyles.caption(context)),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: scoreColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  scoreText,
                  style: TextStyle(fontWeight: FontWeight.w800, color: scoreColor, fontSize: 14),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildLoadingSkeleton() {
    return SingleChildScrollView(
      physics: const NeverScrollableScrollPhysics(),
      child: Column(
        children: [
          Container(
            height: 260,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF0F4C5C), Color(0xFF5F0F40)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(40),
                bottomRight: Radius.circular(40),
              ),
            ),
            child: Center(
              child: CircularProgressIndicator(
                color: Colors.white.withValues(alpha: 0.7),
                strokeWidth: 2.5,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: List.generate(4, (i) => Container(
                margin: const EdgeInsets.only(bottom: 14),
                height: 72,
                decoration: BoxDecoration(
                  color: context.clrBorder.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(20),
                ),
              )),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureActions() {
    final actions = [
      _quickAction(
        title: 'Smart Diagnosis',
        subtitle: 'AI multi-modal scan & advice.',
        icon: Icons.auto_awesome_rounded,
        color: AppColors.primary,
        isPrimary: true,
        onTap: () {
          _openTabOrRoute(1, const InstructionScreen());
        },
      ),
      const SizedBox(height: 14),
      _quickAction(
        title: 'AI Chat',
        subtitle: 'Ask symptoms, treatments, and follow-up questions.',
        icon: Icons.forum_rounded,
        color: AppColors.secondary,
        onTap: () {
          _openTabOrRoute(2, const ChatScreen());
        },
      ),
      _quickAction(
        title: 'Skin Care AI',
        subtitle: 'Personalized routine guide.',
        icon: Icons.face_retouching_natural_rounded,
        color: AppColors.accent,
        onTap: () {
          _openTabOrRoute(3, const SkinCareScreen());
        },
      ),
      _quickAction(
        title: 'Severity Track',
        subtitle: 'Face condition deep-scan.',
        icon: Icons.analytics_rounded,
        color: AppColors.highlight,
        onTap: () {
          _openTabOrRoute(4, const SeverityScreen());
        },
      ),
      _quickAction(
        title: 'Healing Progress',
        subtitle: 'Weekly trends & history.',
        icon: Icons.history_edu_rounded,
        color: AppColors.success,
        onTap: () {
          Navigator.of(
            context,
          ).push(MaterialPageRoute(builder: (_) => const ProgressScreen()));
        },
      ),
    ];

    return LayoutBuilder(
      builder: (context, constraints) {
        final twoColumns = constraints.maxWidth >= 860;
        final spacing = twoColumns ? 14.0 : 0.0;
        final itemWidth = twoColumns
            ? (constraints.maxWidth - spacing) / 2
            : constraints.maxWidth;

        return Wrap(
          spacing: spacing,
          runSpacing: 12,
          children: actions
              .map((action) => SizedBox(width: itemWidth, child: action))
              .toList(),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isEmbeddedHome ? 'Home' : 'Dashboard'),
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
            ? _buildLoadingSkeleton()
            : RefreshIndicator(
                color: AppColors.primary,
                onRefresh: _loadData,
                child: ListView(
                  padding: EdgeInsets.zero,
                  children: [
                    Stack(
                      children: [
                        Container(
                          height: 260,
                          decoration: const BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: [Color(0xFF0F4C5C), Color(0xFF5F0F40)],
                            ),
                            borderRadius: BorderRadius.only(
                              bottomLeft: Radius.circular(40),
                              bottomRight: Radius.circular(40),
                            ),
                          ),
                        ),
                        _framed(
                          context,
                          Padding(
                            padding: const EdgeInsets.fromLTRB(24, 28, 24, 24),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                            decoration: BoxDecoration(
                                              color: Colors.white.withValues(alpha: 0.15),
                                              borderRadius: BorderRadius.circular(20),
                                            ),
                                            child: Text(
                                              '🩺  SKIN HEALTH HUB',
                                              style: TextStyle(
                                                color: Colors.white.withValues(alpha: 0.9),
                                                fontSize: 11,
                                                fontWeight: FontWeight.w800,
                                                letterSpacing: 1.0,
                                              ),
                                            ),
                                          ),
                                          const SizedBox(height: 10),
                                          Text(
                                            'Hello, ${_userName().split(' ').first} 👋',
                                            style: const TextStyle(
                                              color: Colors.white,
                                              fontSize: 30,
                                              fontWeight: FontWeight.w900,
                                              letterSpacing: -0.5,
                                            ),
                                          ),
                                          const SizedBox(height: 4),
                                          Text(
                                            'Your skin care journey continues.',
                                            style: TextStyle(
                                              color: Colors.white.withValues(alpha: 0.72),
                                              fontSize: 14,
                                              fontWeight: FontWeight.w500,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                    Container(
                                      decoration: BoxDecoration(
                                        color: Colors.white.withValues(
                                          alpha: 0.15,
                                        ),
                                        shape: BoxShape.circle,
                                        border: Border.all(
                                          color: Colors.white.withValues(
                                            alpha: 0.2,
                                          ),
                                        ),
                                      ),
                                      child: IconButton(
                                        onPressed: _loadData,
                                        icon: const Icon(
                                          Icons.refresh_rounded,
                                          color: Colors.white,
                                          size: 20,
                                        ),
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
                                const SizedBox(height: 16),
                                Text(
                                  'Overview first. Scan, chat, care, and severity tools are one tap away.',
                                  style: TextStyle(
                                    color: Colors.white.withValues(alpha: 0.8),
                                    fontSize: 13,
                                    fontWeight: FontWeight.w500,
                                    height: 1.4,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    _framed(
                      context,
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildProfilePrompt(),
                            if (_needsProfileSetup) const SizedBox(height: 16),
                            _buildReadinessCard(),
                            if (_validationSummary().isNotEmpty)
                              const SizedBox(height: 16),
                            Text(
                              'Active Journeys',
                              style: AppTextStyles.subHeading(context),
                            ),
                            const SizedBox(height: 16),
                            _buildJourneysSection(),
                            const SizedBox(height: 12),
                            _buildFeatureActions(),
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
