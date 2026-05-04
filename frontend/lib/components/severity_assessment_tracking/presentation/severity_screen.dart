import 'dart:io';

import 'package:app/components/severity_assessment_tracking/data/severity_tracking_api.dart';
import 'package:app/services/supabase_service.dart';
import 'package:app/utils/app_styles.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:app/services/api_service.dart';
import 'package:fl_chart/fl_chart.dart';

class SeverityScreen extends StatefulWidget {
  const SeverityScreen({super.key});

  @override
  State<SeverityScreen> createState() => _SeverityScreenState();
}

class _SeverityScreenState extends State<SeverityScreen> {
  Color get _brand => AppColors.primary;
  Color get _warning => AppColors.warning;

  XFile? _selectedImage;
  bool _isLoading = false;
  bool _isHistoryLoading = true;
  bool _trackProgress = true;
  Map<String, dynamic>? _result;
  List<dynamic> _history = [];
  List<Map<String, dynamic>> _logBooks = [];
  String? _selectedLogBookId;
  String _historyLogBookId = _allLogBooksFilter;
  bool _isCreatingLogBook = false;
  final TextEditingController _descriptionController = TextEditingController();
  final TextEditingController _logBookTitleController = TextEditingController();
  String _logBookBodyPart = 'Face';
  String _logBookFrequency = 'weekly';
  static const List<String> _bodyParts = [
    'Face',
    'Neck',
    'Arm',
    'Leg',
    'Hand',
    'Foot',
    'Back',
    'Chest',
    'Scalp',
  ];
  static const List<String> _frequencies = ['daily', 'weekly'];
  static const String _allLogBooksFilter = '__all_logbooks__';

  @override
  void initState() {
    super.initState();
    _loadLogBooksAndHistory();
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    _logBookTitleController.dispose();
    super.dispose();
  }

  Map<String, dynamic>? get _selectedLogBook {
    for (final item in _logBooks) {
      if (item['id']?.toString() == _selectedLogBookId) return item;
    }
    return null;
  }

  String? get _historyJourneyId =>
      _historyLogBookId == _allLogBooksFilter ? null : _historyLogBookId;

  String _logBookTitleForId(String? id) {
    final normalized = id?.trim();
    if (normalized == null || normalized.isEmpty) return 'No log book';
    for (final item in _logBooks) {
      if (item['id']?.toString() == normalized) {
        return item['title']?.toString() ?? 'Untitled Log Book';
      }
    }
    return 'Unknown Log Book';
  }

  Future<void> _loadHistory() async {
    setState(() => _isHistoryLoading = true);
    final history = await SeverityTrackingApi.getHistory(
      journeyId: _historyJourneyId,
    );
    if (!mounted) return;
    setState(() {
      _history = history;
      _isHistoryLoading = false;
    });
  }

  Future<void> _loadLogBooksAndHistory() async {
    setState(() => _isHistoryLoading = true);
    try {
      final logBooks = await SupabaseService.getJourneys();
      String? selected = _selectedLogBookId;
      if (selected == null && logBooks.isNotEmpty) {
        selected = logBooks.first['id']?.toString();
      }
      final history = await SeverityTrackingApi.getHistory(
        journeyId: _historyJourneyId,
      );
      if (!mounted) return;
      setState(() {
        _logBooks = logBooks;
        _selectedLogBookId = selected;
        _history = history;
        _isHistoryLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _logBooks = [];
        _history = [];
        _isHistoryLoading = false;
      });
    }
  }

  Future<void> _createLogBook() async {
    final title = _logBookTitleController.text.trim();
    if (title.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a log book name.')),
      );
      return;
    }

    setState(() => _isCreatingLogBook = true);
    try {
      final created = await SupabaseService.startJourney(
        title: title,
        bodyPart: _logBookBodyPart,
        frequency: _logBookFrequency,
      );
      if (!mounted) return;
      _logBookTitleController.clear();
      setState(() {
        _selectedLogBookId = created['id']?.toString();
        _historyLogBookId = _allLogBooksFilter;
      });
      await _loadLogBooksAndHistory();
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Log book created.')));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Log book create failed: $e')));
    } finally {
      if (mounted) setState(() => _isCreatingLogBook = false);
    }
  }

  Future<void> _pickImage(ImageSource source) async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: source);
    if (picked == null) return;
    setState(() {
      _selectedImage = picked;
      _result = null;
    });
  }

  Future<void> _analyzeSeverity() async {
    if (_selectedImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a face image first.')),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final bytes = await _selectedImage!.readAsBytes();
      final response = await SeverityTrackingApi.analyzeSeverity(
        bytes,
        _selectedImage!.name,
        track: _trackProgress,
        userId: SupabaseService.userId ?? 'anonymous',
        journeyId: _selectedLogBookId,
        journeyTitle: _selectedLogBook?['title']?.toString(),
        description: _descriptionController.text,
      );
      if (!mounted) return;
      setState(() {
        _result = response;
      });
      await _loadHistory();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Severity analysis failed: $e')));
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _reset() {
    setState(() {
      _selectedImage = null;
      _result = null;
      _trackProgress = true;
      _descriptionController.clear();
    });
  }

  double _toDouble(dynamic value) {
    if (value is num) return value.toDouble();
    return double.tryParse(value?.toString() ?? '') ?? 0.0;
  }

  bool _toBool(dynamic value) {
    if (value is bool) return value;
    if (value is num) return value != 0;
    final normalized = value?.toString().trim().toLowerCase() ?? '';
    return const {'true', '1', 'yes', 'y', 'required'}.contains(normalized);
  }

  Map<String, dynamic> _toMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) {
      return value.map((k, v) => MapEntry(k.toString(), v));
    }
    return {};
  }

  List<String> _toStringList(dynamic value) {
    if (value is! List) return [];
    return value
        .where((item) => item != null)
        .map((item) => item.toString().trim())
        .where((item) => item.isNotEmpty)
        .toList();
  }

  List<Map<String, dynamic>> _toMapList(dynamic value) {
    if (value is! List) return [];
    final output = <Map<String, dynamic>>[];
    for (final item in value) {
      if (item is Map) {
        output.add(item.map((k, v) => MapEntry(k.toString(), v)));
      }
    }
    return output;
  }

  Color _levelColor(String level) {
    final normalized = level.trim().toLowerCase();
    if (normalized == 'mild') return AppColors.success;
    if (normalized == 'medium') return AppColors.warning;
    if (normalized == 'moderate') return AppColors.warning;
    if (normalized == 'severe') return AppColors.error;
    return _brand;
  }

  Widget _sectionCard({
    required String title,
    required Widget child,
    String? subtitle,
    IconData icon = Icons.analytics_outlined,
    Color? accent,
  }) {
    final effectiveAccent = accent ?? _brand;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: AppDecor.softCard(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: effectiveAccent.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, size: 18, color: effectiveAccent),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: AppTextStyles.subHeading(
                    context,
                  ).copyWith(fontSize: 17),
                ),
              ),
            ],
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 6),
            Text(subtitle, style: AppTextStyles.body(context)),
          ],
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }

  Widget _buildUploadView() {
    return Column(
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            gradient: AppGradients.hero,
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: context.isDarkMode
                    ? Colors.black45
                    : const Color(0x1F145563),
                blurRadius: 14,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Face Skin Severity',
                style: AppTextStyles.heading(
                  context,
                ).copyWith(color: Colors.white, fontSize: 24),
              ),
              const SizedBox(height: 8),
              Text(
                'Upload one clear face image. The system extracts engineered skin features and predicts Mild, Moderate, or Severe.',
                style: AppTextStyles.body(
                  context,
                ).copyWith(color: Colors.white.withValues(alpha: 0.9)),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        _buildLogBookCreator(),
        const SizedBox(height: 14),
        _buildLogBookSection(compactWhenEmpty: true),
        const SizedBox(height: 14),
        _sectionCard(
          title: 'Face Image',
          subtitle: 'Use frontal/near-frontal photo with good lighting.',
          icon: Icons.camera_alt_outlined,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              InkWell(
                onTap: () => _pickImage(ImageSource.gallery),
                borderRadius: BorderRadius.circular(14),
                child: Container(
                  width: double.infinity,
                  height: 260,
                  decoration: BoxDecoration(
                    color: context.clrBackground,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: context.clrBorder),
                  ),
                  child: _selectedImage == null
                      ? Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.face_retouching_natural_outlined,
                              size: 54,
                              color: _brand.withValues(alpha: 0.9),
                            ),
                            const SizedBox(height: 10),
                            const Text(
                              'Tap to select selfie',
                              style: TextStyle(fontWeight: FontWeight.w600),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Supported: JPG, JPEG, PNG',
                              style: AppTextStyles.body(context),
                            ),
                          ],
                        )
                      : ClipRRect(
                          borderRadius: BorderRadius.circular(13),
                          child: kIsWeb
                              ? Image.network(
                                  _selectedImage!.path,
                                  fit: BoxFit.cover,
                                )
                              : Image.file(
                                  File(_selectedImage!.path),
                                  fit: BoxFit.cover,
                                ),
                        ),
                ),
              ),
              const SizedBox(height: 14),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: [
                  FilledButton.icon(
                    onPressed: () => _pickImage(ImageSource.camera),
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('Camera'),
                    style: FilledButton.styleFrom(backgroundColor: _brand),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => _pickImage(ImageSource.gallery),
                    icon: const Icon(Icons.photo_library_outlined),
                    label: const Text('Gallery'),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        _sectionCard(
          title: 'Log Book Description',
          subtitle: 'Add daily or weekly notes for this severity entry.',
          icon: Icons.edit_note_outlined,
          child: TextField(
            controller: _descriptionController,
            minLines: 3,
            maxLines: 5,
            textInputAction: TextInputAction.newline,
            decoration: const InputDecoration(
              hintText:
                  'Describe today\'s skin condition, changes, care routine, or symptoms...',
            ),
          ),
        ),
        const SizedBox(height: 14),
        _sectionCard(
          title: 'Tracking',
          subtitle: 'Enable weekly trend tracking for this user profile.',
          icon: Icons.timeline_outlined,
          child: SwitchListTile(
            value: _trackProgress,
            activeThumbColor: AppColors.primary,
            contentPadding: EdgeInsets.zero,
            title: Text(
              _trackProgress ? 'Tracking enabled' : 'Tracking disabled',
              style: AppTextStyles.bodyStrong(context),
            ),
            subtitle: Text(
              _trackProgress
                  ? 'New entries will be saved in visits history.'
                  : 'Only one-time analysis output will be returned.',
              style: AppTextStyles.caption(context),
            ),
            onChanged: (value) {
              setState(() => _trackProgress = value);
            },
          ),
        ),
        const SizedBox(height: 18),
        SizedBox(
          width: double.infinity,
          height: 52,
          child: FilledButton(
            onPressed: _isLoading ? null : _analyzeSeverity,
            child: _isLoading
                ? const SizedBox(
                    height: 22,
                    width: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.2,
                      color: Colors.white,
                    ),
                  )
                : const Text(
                    'Analyze Severity',
                    style: TextStyle(fontWeight: FontWeight.w700),
                  ),
          ),
        ),
      ],
    );
  }

  String _resolveImageUrl(String? rawUrl) {
    if (rawUrl == null || rawUrl.trim().isEmpty) return '';
    final value = rawUrl.trim();
    if (value.startsWith('http://') || value.startsWith('https://')) {
      return value;
    }
    if (value.startsWith('/')) return '${ApiService.baseUrl}$value';
    return value;
  }

  Widget _buildHistoryImage(String? rawUrl) {
    final url = _resolveImageUrl(rawUrl);
    if (url.isEmpty) {
      return const Icon(Icons.hide_image_outlined);
    }
    if (url.startsWith('assets/')) {
      return Image.asset(
        url,
        fit: BoxFit.cover,
        errorBuilder: (context, error, stackTrace) =>
            const Icon(Icons.hide_image_outlined),
      );
    }
    return Image.network(
      url,
      fit: BoxFit.cover,
      errorBuilder: (context, error, stackTrace) =>
          const Icon(Icons.hide_image_outlined),
    );
  }

  List<Map<String, dynamic>> _historyMaps() {
    final rows = <Map<String, dynamic>>[];
    for (final item in _history) {
      if (item is Map) {
        rows.add(item.map((key, value) => MapEntry(key.toString(), value)));
      }
    }
    return rows;
  }

  Widget _buildLogBookSection({bool compactWhenEmpty = false}) {
    final rows = _historyMaps();
    final newestFirst = rows.reversed.toList();
    final showingAll = _historyLogBookId == _allLogBooksFilter;
    final selectedName = showingAll
        ? 'All log books'
        : _logBookTitleForId(_historyLogBookId);
    return _sectionCard(
      title: 'Severity Log Book',
      subtitle: showingAll
          ? 'Combined day-by-day and weekly tracking history from every log book.'
          : '$selectedName history saved in this Severity tab.',
      icon: Icons.menu_book_outlined,
      child: _isHistoryLoading
          ? const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Center(child: CircularProgressIndicator()),
            )
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (_logBooks.isNotEmpty) ...[
                  _buildHistoryFilter(),
                  const SizedBox(height: 16),
                ],
                if (rows.isEmpty)
                  Text(
                    compactWhenEmpty
                        ? 'No entries yet. Create a log book, add a face image and description, then run Analyze Severity.'
                        : 'No severity log book entries yet. Add a face image, description, keep tracking enabled, and run Analyze Severity.',
                    style: AppTextStyles.body(context),
                  )
                else ...[
                  _buildLogTrendChart(rows),
                  const SizedBox(height: 16),
                  ...newestFirst.map(_buildLogBookEntry),
                ],
              ],
            ),
    );
  }

  Widget _buildHistoryFilter() {
    final items = <DropdownMenuItem<String>>[
      const DropdownMenuItem(
        value: _allLogBooksFilter,
        child: Text('All Log Books'),
      ),
      ..._logBooks.map(
        (book) => DropdownMenuItem(
          value: book['id']?.toString(),
          child: Text(
            '${book['title'] ?? 'Untitled Log Book'} - ${book['frequency'] ?? 'weekly'}',
          ),
        ),
      ),
    ];

    return DropdownButtonFormField<String>(
      initialValue: _historyLogBookId,
      isExpanded: true,
      decoration: const InputDecoration(
        labelText: 'Show history',
        prefixIcon: Icon(Icons.history_outlined),
      ),
      items: items,
      onChanged: (value) async {
        if (value == null) return;
        setState(() {
          _historyLogBookId = value;
          _isHistoryLoading = true;
        });
        await _loadHistory();
      },
    );
  }

  Widget _buildLogBookCreator() {
    return _sectionCard(
      title: 'Create Log Book',
      subtitle:
          'Create one log book for a daily or weekly severity tracking history.',
      icon: Icons.add_chart_outlined,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            controller: _logBookTitleController,
            decoration: const InputDecoration(
              labelText: 'Log book name',
              hintText: 'Example: Face eczema weekly tracking',
              prefixIcon: Icon(Icons.book_outlined),
            ),
          ),
          const SizedBox(height: 12),
          LayoutBuilder(
            builder: (context, constraints) {
              final isNarrow = constraints.maxWidth < 720;
              final fields = [
                DropdownButtonFormField<String>(
                  initialValue: _logBookBodyPart,
                  decoration: const InputDecoration(
                    labelText: 'Body part',
                    prefixIcon: Icon(Icons.face_retouching_natural_outlined),
                  ),
                  items: _bodyParts
                      .map(
                        (item) =>
                            DropdownMenuItem(value: item, child: Text(item)),
                      )
                      .toList(),
                  onChanged: (value) {
                    if (value == null) return;
                    setState(() => _logBookBodyPart = value);
                  },
                ),
                DropdownButtonFormField<String>(
                  initialValue: _logBookFrequency,
                  decoration: const InputDecoration(
                    labelText: 'Report frequency',
                    prefixIcon: Icon(Icons.event_repeat_outlined),
                  ),
                  items: _frequencies
                      .map(
                        (item) => DropdownMenuItem(
                          value: item,
                          child: Text(item.toUpperCase()),
                        ),
                      )
                      .toList(),
                  onChanged: (value) {
                    if (value == null) return;
                    setState(() => _logBookFrequency = value);
                  },
                ),
              ];
              if (isNarrow) {
                return Column(
                  children: [fields[0], const SizedBox(height: 12), fields[1]],
                );
              }
              return Row(
                children: [
                  Expanded(child: fields[0]),
                  const SizedBox(width: 12),
                  Expanded(child: fields[1]),
                ],
              );
            },
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            height: 46,
            child: FilledButton.icon(
              onPressed: _isCreatingLogBook ? null : _createLogBook,
              icon: _isCreatingLogBook
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.add),
              label: const Text('Create New Log Book'),
            ),
          ),
          if (_logBooks.isNotEmpty) ...[
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: _selectedLogBookId,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Active log book',
                prefixIcon: Icon(Icons.menu_book_outlined),
                helperText:
                    'New severity scans are saved here. History can still show all log books.',
              ),
              items: _logBooks
                  .map(
                    (book) => DropdownMenuItem(
                      value: book['id']?.toString(),
                      child: Text(
                        '${book['title'] ?? 'Untitled Log Book'} - ${book['frequency'] ?? 'weekly'}',
                      ),
                    ),
                  )
                  .toList(),
              onChanged: (value) async {
                setState(() {
                  _selectedLogBookId = value;
                  _isHistoryLoading = true;
                });
                await _loadHistory();
              },
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildLogTrendChart(List<Map<String, dynamic>> rows) {
    final spots = <FlSpot>[];
    for (var i = 0; i < rows.length; i++) {
      spots.add(
        FlSpot(
          i.toDouble(),
          _toDouble(rows[i]['score']).clamp(0.0, 100.0).toDouble(),
        ),
      );
    }

    return Container(
      height: 220,
      padding: const EdgeInsets.fromLTRB(12, 18, 12, 10),
      decoration: BoxDecoration(
        color: context.clrSurface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: context.clrBorder),
      ),
      child: LineChart(
        LineChartData(
          minY: 0,
          maxY: 100,
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            horizontalInterval: 25,
            getDrawingHorizontalLine: (_) => FlLine(
              color: context.clrBorder.withValues(alpha: 0.55),
              strokeWidth: 1,
            ),
          ),
          borderData: FlBorderData(show: false),
          titlesData: FlTitlesData(
            topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 34,
                interval: 25,
                getTitlesWidget: (value, _) => Text(
                  value.toInt().toString(),
                  style: AppTextStyles.caption(context),
                ),
              ),
            ),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 24,
                interval: 1,
                getTitlesWidget: (value, _) {
                  final index = value.toInt();
                  if (index < 0 || index >= rows.length) {
                    return const SizedBox.shrink();
                  }
                  return Text(
                    '${index + 1}',
                    style: AppTextStyles.caption(context),
                  );
                },
              ),
            ),
          ),
          lineBarsData: [
            LineChartBarData(
              spots: spots,
              isCurved: spots.length > 2,
              color: AppColors.primary,
              barWidth: 3,
              dotData: FlDotData(show: true),
              belowBarData: BarAreaData(
                show: true,
                color: AppColors.primary.withValues(alpha: 0.10),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLogBookEntry(Map<String, dynamic> entry) {
    final status = (entry['status'] ?? 'Unknown').toString();
    final score = _toDouble(entry['score']);
    final description = (entry['description'] ?? '').toString().trim();
    final metrics = _toMap(entry['metrics']);
    final logBookTitle = _logBookTitleForId(entry['journey_id']?.toString());
    final showLogBookName = _historyLogBookId == _allLogBooksFilter;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: context.clrSurface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: context.clrBorder),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: Container(
              width: 92,
              height: 92,
              color: context.clrBackgroundAlt,
              child: _buildHistoryImage(entry['image_url']?.toString()),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        '${entry['week'] ?? 'Visit'} - $status',
                        style: AppTextStyles.bodyStrong(context),
                      ),
                    ),
                    Text(
                      '${score.toStringAsFixed(0)}%',
                      style: AppTextStyles.bodyStrong(
                        context,
                      ).copyWith(color: _levelColor(status)),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  (entry['date'] ?? entry['timestamp'] ?? '').toString(),
                  style: AppTextStyles.caption(context),
                ),
                if (showLogBookName) ...[
                  const SizedBox(height: 6),
                  _chip(logBookTitle),
                ],
                const SizedBox(height: 8),
                Text(
                  description.isEmpty ? 'No description added.' : description,
                  style: AppTextStyles.body(context),
                ),
                if (metrics.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _chip(
                        'Redness ${_toDouble(metrics['redness']).toStringAsFixed(1)}',
                      ),
                      _chip(
                        'Inflammation ${_toDouble(metrics['inflammation']).toStringAsFixed(1)}',
                      ),
                      _chip(
                        'Scaling ${_toDouble(metrics['scaling']).toStringAsFixed(1)}',
                      ),
                      _chip(
                        'Texture ${_toDouble(metrics['texture']).toStringAsFixed(1)}',
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildReviewBanner({
    required String validationStatus,
    required String analysisScope,
    required bool requiresReview,
    required String? trackingBlockedReason,
    required List<String> reviewReasons,
  }) {
    final title = requiresReview
        ? 'Review recommended'
        : 'Operational validation only';
    final message = validationStatus == 'operational_only_unlabeled'
        ? 'This severity model passed operational checks, but there is no local labeled severity benchmark for a formal clinical accuracy claim.'
        : 'Use this severity result as a screening/tracking aid only.';

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
              _chip('Scope: $analysisScope'),
              if (trackingBlockedReason != null &&
                  trackingBlockedReason.isNotEmpty)
                _chip('Tracking blocked'),
            ],
          ),
          if (trackingBlockedReason != null &&
              trackingBlockedReason.isNotEmpty) ...[
            const SizedBox(height: 10),
            Text(trackingBlockedReason, style: AppTextStyles.body(context)),
          ],
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

  Widget _buildResultView() {
    final result = _result ?? {};
    final level = (result['severity_level'] ?? 'Moderate').toString();
    final score = _toDouble(result['severity_score']);
    final confidence = _toDouble(result['confidence']);
    final probabilities = _toMap(result['probabilities']);
    final thresholds = _toMap(result['thresholds']);
    final preprocessing = _toMap(result['preprocessing']);
    final featureVector = _toMap(result['feature_vector']);
    final normalizedFeatures = _toMap(result['normalized_features']);
    final tracking = _toMap(result['tracking']);
    final weeklyTrend = _toMapList(tracking['weekly_trend']);
    final validationStatus = (result['validation_status'] ?? '').toString();
    final analysisScope = (result['analysis_scope'] ?? '').toString();
    final requiresReview = _toBool(result['requires_review']);
    final reviewReasons = _toStringList(result['review_reasons']);
    final nextSteps = _toStringList(result['next_steps']);
    final limitations = _toStringList(result['limitations']);
    final qualityNotes = _toStringList(result['quality_notes']);
    final trackingBlockedReason = result['tracking_blocked_reason']?.toString();

    // Smart Guard Fields
    final clinicalRationale = (result['clinical_rationale'] ?? '').toString();
    final healingInsight = (result['healing_insight'] ?? '').toString();
    final identifiedBodyPart = (result['identified_body_part'] ?? '')
        .toString();
    final isConsistent = _toBool(result['is_consistent_with_journey'] ?? true);
    final consistencyWarning = (result['consistency_warning'] ?? '').toString();
    final visitNumber = result['visit_number'] ?? 1;
    final currentImageUrl = result['current_image_url']?.toString();
    final baselineImageUrl = result['baseline_image_url']?.toString();

    final baseUrl = ApiService.baseUrl;

    final levelColor = _levelColor(level);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            gradient: LinearGradient(
              colors: [levelColor, levelColor.withValues(alpha: 0.72)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Severity Level',
                style: AppTextStyles.caption(
                  context,
                ).copyWith(color: Colors.white70),
              ),
              const SizedBox(height: 4),
              Text(
                level,
                style: AppTextStyles.heading(
                  context,
                ).copyWith(color: Colors.white, fontSize: 34),
              ),
              const SizedBox(height: 10),
              Text(
                'Severity Score: ${score.toStringAsFixed(1)} / 100',
                style: AppTextStyles.bodyStrong(
                  context,
                ).copyWith(color: Colors.white),
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: LinearProgressIndicator(
                  minHeight: 8,
                  value: (score / 100).clamp(0.0, 1.0),
                  backgroundColor: Colors.white.withValues(alpha: 0.26),
                  color: Colors.white,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        // --- SMART GUARD: Consistency Warning ---
        if (!isConsistent && consistencyWarning.isNotEmpty) ...[
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.error.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.error.withValues(alpha: 0.4)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.warning_amber_rounded, color: AppColors.error),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Body Part Mismatch',
                        style: AppTextStyles.bodyStrong(
                          context,
                        ).copyWith(color: AppColors.error),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        consistencyWarning,
                        style: AppTextStyles.body(context),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
        ],

        // --- SMART GUARD: Clinical Rationale & Healing Insight ---
        if (clinicalRationale.isNotEmpty) ...[
          _sectionCard(
            title: 'Clinical Advisory',
            subtitle:
                'AI-driven rationale for visit #$visitNumber ($identifiedBodyPart)',
            icon: Icons.medical_services_outlined,
            accent: Colors.blueAccent,
            child: MarkdownBody(
              data: clinicalRationale,
              styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context))
                  .copyWith(
                    p: AppTextStyles.body(
                      context,
                    ).copyWith(fontSize: 15, height: 1.5),
                  ),
            ),
          ),
          const SizedBox(height: 14),
        ],

        // --- SMART GUARD: Visual Comparison Gallery ---
        if (baselineImageUrl != null) ...[
          _sectionCard(
            title: 'Visual Progress',
            subtitle: 'Day 1 Baseline vs. Current Scan',
            icon: Icons.compare_outlined,
            accent: Colors.orangeAccent,
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(10),
                            child: Image.network(
                              '$baseUrl$baselineImageUrl',
                              height: 150,
                              width: double.infinity,
                              fit: BoxFit.cover,
                              errorBuilder: (context, error, stackTrace) =>
                                  Container(
                                    height: 150,
                                    color: context.clrBackgroundAlt,
                                    child: const Icon(
                                      Icons.broken_image_outlined,
                                    ),
                                  ),
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            'Baseline',
                            style: AppTextStyles.caption(context),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(10),
                            child: currentImageUrl != null
                                ? Image.network(
                                    '$baseUrl$currentImageUrl',
                                    height: 150,
                                    width: double.infinity,
                                    fit: BoxFit.cover,
                                  )
                                : Container(
                                    height: 150,
                                    color: context.clrBackgroundAlt,
                                    child: const Center(child: Text('Current')),
                                  ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            'Current',
                            style: AppTextStyles.caption(context),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                if (healingInsight.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.orangeAccent.withValues(alpha: 0.05),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: Colors.orangeAccent.withValues(alpha: 0.1),
                      ),
                    ),
                    child: Text(
                      healingInsight,
                      style: AppTextStyles.bodyStrong(context).copyWith(
                        color: context.isDarkMode
                            ? Colors.orange[200]
                            : Colors.orange[800],
                        fontStyle: FontStyle.italic,
                        fontSize: 13,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 14),
        ] else if (healingInsight.isNotEmpty) ...[
          // Fallback if we have text but no image URL yet
          _sectionCard(
            title: 'Healing Journey',
            subtitle: 'Comparison with your Day 1 baseline scan.',
            icon: Icons.auto_awesome_outlined,
            accent: Colors.purpleAccent,
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.purpleAccent.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: Colors.purpleAccent.withValues(alpha: 0.1),
                ),
              ),
              child: Text(
                healingInsight,
                style: AppTextStyles.bodyStrong(context).copyWith(
                  color: context.isDarkMode
                      ? Colors.purple[200]
                      : Colors.purple[800],
                  fontStyle: FontStyle.italic,
                ),
              ),
            ),
          ),
          const SizedBox(height: 14),
        ],

        if (validationStatus.isNotEmpty ||
            requiresReview ||
            (trackingBlockedReason?.isNotEmpty ?? false)) ...[
          _buildReviewBanner(
            validationStatus: validationStatus,
            analysisScope: analysisScope,
            requiresReview: requiresReview,
            trackingBlockedReason: trackingBlockedReason,
            reviewReasons: reviewReasons,
          ),
          const SizedBox(height: 14),
        ],
        _sectionCard(
          title: 'Prediction Confidence',
          subtitle: 'RandomForest class probabilities.',
          icon: Icons.query_stats_outlined,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Top confidence: ${(confidence * 100).toStringAsFixed(1)}%',
                style: AppTextStyles.bodyStrong(context),
              ),
              const SizedBox(height: 10),
              ...probabilities.entries.map((entry) {
                final p = _toDouble(entry.value);
                return Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${entry.key}: ${(p * 100).toStringAsFixed(1)}%',
                        style: AppTextStyles.bodyStrong(context),
                      ),
                      const SizedBox(height: 6),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: LinearProgressIndicator(
                          minHeight: 7,
                          value: p.clamp(0.0, 1.0),
                          color: AppColors.primary,
                          backgroundColor: context.clrBackgroundAlt,
                        ),
                      ),
                    ],
                  ),
                );
              }),
            ],
          ),
        ),
        const SizedBox(height: 14),
        _sectionCard(
          title: 'Score Thresholds',
          subtitle: 'Metadata-driven grading boundaries.',
          icon: Icons.tune_outlined,
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _chip('q1: ${_toDouble(thresholds['q1']).toStringAsFixed(2)}'),
              _chip('q2: ${_toDouble(thresholds['q2']).toStringAsFixed(2)}'),
              _chip('Score: ${score.toStringAsFixed(2)}'),
            ],
          ),
        ),
        const SizedBox(height: 14),
        if (nextSteps.isNotEmpty)
          _sectionCard(
            title: 'Next Steps',
            subtitle: 'Actions to improve reliability or escalate safely.',
            icon: Icons.checklist_outlined,
            accent: _brand,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: nextSteps
                  .map(
                    (step) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(
                            Icons.chevron_right,
                            size: 18,
                            color: AppColors.primary,
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              step,
                              style: AppTextStyles.body(context),
                            ),
                          ),
                        ],
                      ),
                    ),
                  )
                  .toList(),
            ),
          ),
        if (nextSteps.isNotEmpty) const SizedBox(height: 14),
        if (qualityNotes.isNotEmpty)
          _sectionCard(
            title: 'Quality Notes',
            subtitle:
                'Automatic input-quality observations from preprocessing.',
            icon: Icons.image_search_outlined,
            accent: _warning,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: qualityNotes
                  .map(
                    (note) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(note, style: AppTextStyles.body(context)),
                    ),
                  )
                  .toList(),
            ),
          ),
        if (qualityNotes.isNotEmpty) const SizedBox(height: 14),
        if (limitations.isNotEmpty)
          _sectionCard(
            title: 'Limitations',
            subtitle: 'Important scope limits for interpreting this result.',
            icon: Icons.rule_outlined,
            accent: _warning,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: limitations
                  .map(
                    (item) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(item, style: AppTextStyles.body(context)),
                    ),
                  )
                  .toList(),
            ),
          ),
        if (limitations.isNotEmpty) const SizedBox(height: 14),
        _sectionCard(
          title: 'Preprocessing',
          subtitle: 'Image quality and pipeline metadata.',
          icon: Icons.photo_filter_outlined,
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _chip('Normalization: ${preprocessing['normalization'] ?? '-'}'),
              _chip(
                'Face visible: ${preprocessing['face_visible'] ?? 'unknown'}',
              ),
              _chip('Face count: ${preprocessing['face_count'] ?? 'unknown'}'),
              _chip(
                'Input: ${_toMap(preprocessing['input_size'])['width'] ?? '-'}x${_toMap(preprocessing['input_size'])['height'] ?? '-'}',
              ),
              _chip(
                'Target: ${_toMap(preprocessing['target_size'])['width'] ?? '-'}x${_toMap(preprocessing['target_size'])['height'] ?? '-'}',
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        _sectionCard(
          title: 'Extracted Features',
          subtitle: 'Raw engineered values from the image.',
          icon: Icons.dataset_outlined,
          child: _buildFeatureTable(featureVector),
        ),
        const SizedBox(height: 14),
        _sectionCard(
          title: 'Normalized Features',
          subtitle: 'Min-max scaled values used for model input.',
          icon: Icons.stacked_bar_chart_outlined,
          child: _buildFeatureTable(normalizedFeatures),
        ),
        const SizedBox(height: 14),
        if ((_result?['tracking_enabled'] ?? false) == true)
          _sectionCard(
            title: 'Progress Tracking',
            subtitle: 'Weekly trend for this user id.',
            icon: Icons.timeline,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (tracking['visits_count'] != null)
                  Text(
                    'Visits: ${tracking['visits_count']} | Improvement: ${tracking['improvement_percent'] ?? 0}%',
                    style: AppTextStyles.bodyStrong(context),
                  ),
                const SizedBox(height: 8),
                if (weeklyTrend.isEmpty)
                  Text(
                    'No weekly trend available yet.',
                    style: AppTextStyles.body(context),
                  )
                else
                  ...weeklyTrend.map(
                    (row) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              row['week']?.toString() ?? '-',
                              style: AppTextStyles.bodyStrong(context),
                            ),
                          ),
                          Text(
                            _toDouble(
                              row['avg_severity_score'],
                            ).toStringAsFixed(1),
                            style: AppTextStyles.body(context),
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        const SizedBox(height: 14),
        _buildLogBookSection(),
        const SizedBox(height: 20),
        SizedBox(
          width: double.infinity,
          height: 50,
          child: OutlinedButton.icon(
            onPressed: _reset,
            icon: const Icon(Icons.refresh),
            label: const Text('Analyze Another Photo'),
          ),
        ),
      ],
    );
  }

  Widget _chip(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: context.clrBackgroundAlt,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: context.clrBorder),
      ),
      child: Text(
        text,
        style: AppTextStyles.caption(
          context,
        ).copyWith(fontSize: 13, color: context.clrTextMain),
      ),
    );
  }

  Widget _buildFeatureTable(Map<String, dynamic> values) {
    if (values.isEmpty) {
      return Text('No data available.', style: AppTextStyles.body(context));
    }
    final entries = values.entries.toList();
    entries.sort((a, b) => a.key.compareTo(b.key));
    return Column(
      children: entries
          .map(
            (entry) => Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(10),
                color: context.clrSurface,
                border: Border.all(color: context.clrBorder),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      entry.key,
                      style: AppTextStyles.bodyStrong(
                        context,
                      ).copyWith(fontSize: 13.5, color: context.clrTextMain),
                    ),
                  ),
                  Text(
                    _toDouble(entry.value).toStringAsFixed(4),
                    style: AppTextStyles.body(
                      context,
                    ).copyWith(fontSize: 13.5, color: context.clrTextSec),
                  ),
                ],
              ),
            ),
          )
          .toList(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Severity Analysis')),
      body: Container(
        decoration: BoxDecoration(gradient: AppGradients.page(context)),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 20),
            child: _result == null ? _buildUploadView() : _buildResultView(),
          ),
        ),
      ),
    );
  }
}
