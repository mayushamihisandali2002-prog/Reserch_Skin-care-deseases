import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/app_styles.dart';

//
// DATA MODELS
//

enum MessageSender { user, bot }

/// Holds a single conversation turn.
class ChatMessage {
  final MessageSender sender;
  final String text;
  final Map<String, dynamic>? apiResponse; // full JSON for bot AI replies
  final DateTime timestamp;

  const ChatMessage({
    required this.sender,
    required this.text,
    this.apiResponse,
    required this.timestamp,
  });
}

//
// SCREEN
//

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with TickerProviderStateMixin {
  // Messages list
  final List<ChatMessage> _messages = [
    ChatMessage(
      sender: MessageSender.bot,
      text:
          'Hello! I\'m your AI Skin Care Assistant.\n\n'
          'I can help identify skin conditions, suggest treatments, '
          'and answer your questions about skin health.\n\n'
          'How can I help you today?',
      timestamp: DateTime.now(),
    ),
  ];

  // Input / UX state
  final TextEditingController _controller = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  final ScrollController _scrollController = ScrollController();

  bool _isTyping = false;
  bool _isConnected = true;
  String? _followupPlaceholder; // set when user taps a follow-up chip
  String? _lastDisease;

  // Typing dots animation
  late AnimationController _dotController;
  late Animation<double> _dotAnimation;

  @override
  void initState() {
    super.initState();
    _dotController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);
    _dotAnimation = Tween<double>(begin: 0.3, end: 1.0).animate(_dotController);
  }

  @override
  void dispose() {
    _dotController.dispose();
    _controller.dispose();
    _focusNode.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  //
  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 350),
          curve: Curves.easeOut,
        );
      }
    });
  }

  //
  Future<void> _sendMessage({String? override}) async {
    final text = override ?? _controller.text.trim();
    if (text.isEmpty || _isTyping) return;

    setState(() {
      _messages.add(
        ChatMessage(
          sender: MessageSender.user,
          text: text,
          timestamp: DateTime.now(),
        ),
      );
      _isTyping = true;
      _followupPlaceholder = null;
      _controller.clear();
    });
    _scrollToBottom();

    try {
      final response = await ApiService.sendChatMessage(text);
      if (!mounted) return;

      // Cache last predicted state for status bar
      final disease = response['predicted_disease'] as String?;
      if (disease != null && disease != 'Unable to determine') {
        _lastDisease = disease;
      }

      setState(() {
        _messages.add(
          ChatMessage(
            sender: MessageSender.bot,
            text: response['reply'] as String? ?? 'No response',
            apiResponse: response,
            timestamp: DateTime.now(),
          ),
        );
        _isConnected = true;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isConnected = false;
        _messages.add(
          ChatMessage(
            sender: MessageSender.bot,
            text:
                'Could not connect to the assistant. Please check your '
                'connection and tap Retry.',
            apiResponse: {'_error': true, '_originalText': text},
            timestamp: DateTime.now(),
          ),
        );
      });
    } finally {
      if (mounted) {
        setState(() => _isTyping = false);
        _scrollToBottom();
      }
    }
  }

  //
  // BUILD
  //

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => FocusScope.of(context).unfocus(),
      child: DecoratedBox(
        decoration: const BoxDecoration(gradient: AppGradients.page),
        child: Column(
          children: [
            _buildHeader(),
            if (_lastDisease != null) _buildDiagnosisBanner(),
            Expanded(child: _buildMessageList()),
            if (_isTyping) _buildTypingIndicator(),
            if (!_isConnected) _buildOfflineBanner(),
            _buildInputBar(),
          ],
        ),
      ),
    );
  }

  //
  Widget _buildHeader() {
    return Container(
      decoration: BoxDecoration(
        gradient: AppGradients.hero,
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.30),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 14),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.18),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.medical_services_outlined,
                  color: Colors.white,
                  size: 22,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'AI Skin Care Assistant',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                        fontSize: 16,
                        letterSpacing: 0.2,
                      ),
                    ),
                    Row(
                      children: [
                        Container(
                          width: 7,
                          height: 7,
                          decoration: BoxDecoration(
                            color: _isConnected
                                ? const Color(0xFF4ADE80)
                                : AppColors.warning,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 5),
                        Text(
                          _isConnected
                              ? 'AI assistant online'
                              : 'Reconnecting...',
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.85),
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(
                  Icons.refresh_rounded,
                  color: Colors.white,
                  size: 22,
                ),
                tooltip: 'Clear chat',
                onPressed: _clearChat,
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _clearChat() {
    setState(() {
      _messages.clear();
      _lastDisease = null;
      _messages.add(
        ChatMessage(
          sender: MessageSender.bot,
          text:
              'Chat cleared. Describe your symptoms and I\'ll help diagnose your '
              'skin condition.',
          timestamp: DateTime.now(),
        ),
      );
    });
  }

  //
  Widget _buildDiagnosisBanner() {
    const color = AppColors.primaryDark;
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      margin: const EdgeInsets.fromLTRB(14, 12, 14, 0),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.09),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.24)),
      ),
      child: Row(
        children: [
          const Icon(Icons.biotech_outlined, size: 16, color: color),
          const SizedBox(width: 8),
          Text(
            'Active diagnosis: ',
            style: TextStyle(fontSize: 12, color: Colors.grey[700]),
          ),
          Text(
            _lastDisease ?? '',
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: color,
            ),
          ),
          const Spacer(),
        ],
      ),
    );
  }

  // Message list
  Widget _buildMessageList() {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 8),
      itemCount: _messages.length,
      itemBuilder: (_, i) => _buildMessageItem(_messages[i]),
    );
  }

  Widget _buildMessageItem(ChatMessage msg) {
    if (msg.sender == MessageSender.user) {
      return _UserBubble(message: msg);
    }
    // Bot: check for error flag
    final isError = msg.apiResponse?['_error'] == true;
    if (isError) {
      return _ErrorBubble(
        message: msg,
        onRetry: () {
          final orig = msg.apiResponse?['_originalText'] as String?;
          if (orig != null) _sendMessage(override: orig);
        },
      );
    }
    return _BotResponseCard(
      message: msg,
      onFollowupTap: (question) {
        setState(() => _followupPlaceholder = question);
        _focusNode.requestFocus();
      },
    );
  }

  //
  Widget _buildTypingIndicator() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 0, 8),
      child: Row(
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.12),
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.medical_services_outlined,
              size: 18,
              color: AppColors.primary,
            ),
          ),
          const SizedBox(width: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.98),
              borderRadius: BorderRadius.circular(
                20,
              ).copyWith(bottomLeft: Radius.zero),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.06),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: _DotsAnimation(animation: _dotAnimation),
          ),
        ],
      ),
    );
  }

  //
  Widget _buildOfflineBanner() {
    return Container(
      margin: const EdgeInsets.fromLTRB(14, 0, 14, 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.warning.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.warning.withValues(alpha: 0.35)),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.wifi_off_rounded,
            color: AppColors.warning,
            size: 18,
          ),
          const SizedBox(width: 8),
          const Expanded(
            child: Text(
              'Connection issue. Check that the backend server is running.',
              style: TextStyle(color: AppColors.warning, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }

  // Input bar
  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 20),
      decoration: BoxDecoration(
        color: AppColors.surface.withValues(alpha: 0.98),
        border: Border(
          top: BorderSide(color: AppColors.border.withValues(alpha: 0.8)),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 16,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: Container(
                constraints: const BoxConstraints(maxHeight: 120),
                decoration: BoxDecoration(
                  color: AppColors.backgroundAlt.withValues(alpha: 0.85),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(
                    color: _focusNode.hasFocus
                        ? AppColors.primary
                        : AppColors.border,
                    width: _focusNode.hasFocus ? 2 : 1,
                  ),
                ),
                child: TextField(
                  controller: _controller,
                  focusNode: _focusNode,
                  maxLines: 5,
                  minLines: 1,
                  textCapitalization: TextCapitalization.sentences,
                  textInputAction: TextInputAction.send,
                  style: const TextStyle(
                    fontSize: 15,
                    height: 1.4,
                    color: AppColors.textMain,
                  ),
                  decoration: InputDecoration(
                    hintText:
                        _followupPlaceholder ?? 'Type your symptoms here...',
                    hintStyle: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 15,
                    ),
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 20,
                      vertical: 14,
                    ),
                  ),
                  onSubmitted: (_) => _sendMessage(),
                  onChanged: (_) => setState(() {}),
                ),
              ),
            ),
            const SizedBox(width: 12),
            _SendButton(
              onTap: _isTyping || _controller.text.trim().isEmpty
                  ? null
                  : () => _sendMessage(),
              isTyping: _isTyping,
              hasText: _controller.text.trim().isNotEmpty,
            ),
          ],
        ),
      ),
    );
  }
}

//
// SUB-WIDGETS
//

/// User message bubble (right-aligned, gradient).
class _UserBubble extends StatelessWidget {
  final ChatMessage message;
  const _UserBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.only(bottom: 14, left: 64),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [AppColors.primaryDark, AppColors.primary],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
            bottomLeft: Radius.circular(20),
            bottomRight: Radius.circular(4),
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.primaryDark.withValues(alpha: 0.28),
              blurRadius: 8,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Text(
          message.text,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 14,
            height: 1.4,
          ),
        ),
      ),
    );
  }
}

/// Bot AI response card with all rich information panels.
class _BotResponseCard extends StatefulWidget {
  final ChatMessage message;
  final void Function(String question) onFollowupTap;

  const _BotResponseCard({required this.message, required this.onFollowupTap});

  @override
  State<_BotResponseCard> createState() => _BotResponseCardState();
}

class _BotResponseCardState extends State<_BotResponseCard>
    with SingleTickerProviderStateMixin {
  bool _treatmentsExpanded = false;
  late AnimationController _fadeCtrl;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _fadeCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    )..forward();
    _fadeAnim = CurvedAnimation(parent: _fadeCtrl, curve: Curves.easeOut);
  }

  @override
  void dispose() {
    _fadeCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final resp = widget.message.apiResponse;
    final hasApiData = resp != null && resp['_error'] != true;

    final reply = widget.message.text;
    final disease = hasApiData ? resp['predicted_disease'] as String? : null;
    final treatments = hasApiData
        ? (resp['recommended_treatments'] as List<dynamic>?) ?? []
        : <dynamic>[];
    final followUps = hasApiData
        ? (resp['follow_up_questions'] as List<dynamic>?) ?? []
        : <dynamic>[];
    final needsMoreInfo = hasApiData
        ? resp['needs_more_info'] as bool? ?? false
        : false;

    final showDisease = disease != null && disease != 'Unable to determine';

    return FadeTransition(
      opacity: _fadeAnim,
      child: Align(
        alignment: Alignment.centerLeft,
        child: Container(
          margin: const EdgeInsets.only(bottom: 16, right: 48),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Bot avatar
              Container(
                width: 34,
                height: 34,
                margin: const EdgeInsets.only(top: 2, right: 10),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [AppColors.primary, AppColors.secondary],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.medical_services_outlined,
                  color: Colors.white,
                  size: 18,
                ),
              ),

              Flexible(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    //
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.surface.withValues(alpha: 0.96),
                        borderRadius: const BorderRadius.only(
                          topLeft: Radius.circular(4),
                          topRight: Radius.circular(20),
                          bottomLeft: Radius.circular(20),
                          bottomRight: Radius.circular(20),
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.06),
                            blurRadius: 10,
                            offset: const Offset(0, 3),
                          ),
                        ],
                      ),
                      child: _FormattedText(text: reply),
                    ),

                    //
                    if (showDisease) ...[
                      const SizedBox(height: 10),
                      _DiseaseBadge(disease: disease),
                    ],

                    //
                    if (treatments.isNotEmpty && showDisease) ...[
                      const SizedBox(height: 10),
                      _TreatmentsPanel(
                        treatments: treatments,
                        expanded: _treatmentsExpanded,
                        onToggle: () => setState(
                          () => _treatmentsExpanded = !_treatmentsExpanded,
                        ),
                      ),
                    ],

                    //
                    if (followUps.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      _FollowUpChips(
                        questions: followUps.cast<String>(),
                        label: needsMoreInfo
                            ? 'Help me understand better:'
                            : 'You might also ask:',
                        onTap: widget.onFollowupTap,
                      ),
                    ],

                    //
                    Padding(
                      padding: const EdgeInsets.only(top: 6, left: 2),
                      child: Text(
                        _formatTime(widget.message.timestamp),
                        style: TextStyle(fontSize: 10, color: Colors.grey[400]),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatTime(DateTime t) =>
      '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
}

/// Error bubble with retry button.
class _ErrorBubble extends StatelessWidget {
  final ChatMessage message;
  final VoidCallback onRetry;
  const _ErrorBubble({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 14, right: 48),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.error.withValues(alpha: 0.10),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.error.withValues(alpha: 0.36)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(
                  Icons.wifi_off_rounded,
                  size: 16,
                  color: AppColors.error,
                ),
                const SizedBox(width: 8),
                Text(
                  'Could not reach server',
                  style: TextStyle(
                    color: AppColors.error.withValues(alpha: 0.9),
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              message.text,
              style: const TextStyle(color: AppColors.error, fontSize: 12),
            ),
            const SizedBox(height: 10),
            GestureDetector(
              onTap: onRetry,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: AppColors.error,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text(
                  'Retry',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

//
// REUSABLE COMPONENTS
//

/// Renders plain text with simple **bold** support.
class _FormattedText extends StatelessWidget {
  final String text;
  const _FormattedText({required this.text});

  @override
  Widget build(BuildContext context) {
    final spans = <TextSpan>[];
    final parts = text.split('**');
    for (int i = 0; i < parts.length; i++) {
      spans.add(
        TextSpan(
          text: parts[i],
          style: TextStyle(
            fontWeight: i.isOdd ? FontWeight.w700 : FontWeight.normal,
            color: Colors.black87,
            fontSize: 13.5,
            height: 1.55,
          ),
        ),
      );
    }
    return SelectableText.rich(TextSpan(children: spans));
  }
}

/// Disease prediction badge with confidence bar.
class _DiseaseBadge extends StatelessWidget {
  final String disease;

  const _DiseaseBadge({required this.disease});

  @override
  Widget build(BuildContext context) {
    // Simplified badge without confidence display
    const color = AppColors.primaryDark;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            color.withValues(alpha: 0.12),
            color.withValues(alpha: 0.04),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.verified, size: 18, color: color),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Identified Condition',
                  style: TextStyle(
                    fontSize: 10,
                    color: Colors.grey,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  disease,
                  style: const TextStyle(
                    color: color,
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Expandable treatments panel.
class _TreatmentsPanel extends StatelessWidget {
  final List<dynamic> treatments;
  final bool expanded;
  final VoidCallback onToggle;

  const _TreatmentsPanel({
    required this.treatments,
    required this.expanded,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    final shown = expanded ? treatments : treatments.take(2).toList();

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFF0FDF4),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF86EFAC)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 8),
            child: Row(
              children: [
                const Icon(
                  Icons.local_pharmacy_outlined,
                  size: 16,
                  color: Color(0xFF16A34A),
                ),
                const SizedBox(width: 6),
                const Expanded(
                  child: Text(
                    'Treatment Options',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 13,
                      color: Color(0xFF15803D),
                    ),
                  ),
                ),
                GestureDetector(
                  onTap: onToggle,
                  child: Row(
                    children: [
                      Text(
                        expanded ? 'Less' : 'All ${treatments.length}',
                        style: const TextStyle(
                          fontSize: 11,
                          color: Color(0xFF16A34A),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Icon(
                        expanded
                            ? Icons.keyboard_arrow_up
                            : Icons.keyboard_arrow_down,
                        size: 16,
                        color: const Color(0xFF16A34A),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          // Treatment items
          ...shown.map((t) {
            final medicine = t is Map
                ? (t['medicine'] as String? ?? 'Unknown')
                : t.toString();
            final advice = t is Map ? (t['advice'] as String? ?? '') : '';
            return Padding(
              padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    margin: const EdgeInsets.only(top: 3),
                    width: 6,
                    height: 6,
                    decoration: const BoxDecoration(
                      color: Color(0xFF16A34A),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          medicine,
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFF166534),
                          ),
                        ),
                        if (advice.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 2),
                            child: Text(
                              advice,
                              style: TextStyle(
                                fontSize: 11,
                                color: Colors.grey[600],
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}

/// Follow-up suggestion chips.
//
class _FollowUpChips extends StatelessWidget {
  final List<String> questions;
  final String label;
  final void Function(String) onTap;

  const _FollowUpChips({
    required this.questions,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 12,
            color: Color(0xFF6B7280),
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: questions.map((q) {
            return GestureDetector(
              onTap: () => onTap(q),
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: AppColors.primary.withValues(alpha: 0.4),
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.08),
                      blurRadius: 4,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.touch_app_outlined,
                      size: 12,
                      color: AppColors.primary,
                    ),
                    const SizedBox(width: 5),
                    Text(
                      q,
                      style: TextStyle(
                        fontSize: 12,
                        color: AppColors.primary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }
}

/// Animated send button.
class _SendButton extends StatelessWidget {
  final VoidCallback? onTap;
  final bool isTyping;
  final bool hasText;
  const _SendButton({
    required this.onTap,
    required this.isTyping,
    this.hasText = true,
  });

  @override
  Widget build(BuildContext context) {
    final bool isDisabled = isTyping || !hasText;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: 52,
        height: 52,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: isDisabled
                ? [const Color(0xFFE5E7EB), const Color(0xFFD1D5DB)]
                : [AppColors.primary, AppColors.primaryDark],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          shape: BoxShape.circle,
          boxShadow: isDisabled
              ? []
              : [
                  BoxShadow(
                    color: AppColors.primary.withValues(alpha: 0.35),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
        ),
        child: Center(
          child: isTyping
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.5,
                    color: Colors.white,
                  ),
                )
              : Icon(
                  Icons.send_rounded,
                  color: isDisabled ? const Color(0xFF9CA3AF) : Colors.white,
                  size: 22,
                ),
        ),
      ),
    );
  }
}

/// Three bouncing dots typing animation.
class _DotsAnimation extends StatelessWidget {
  final Animation<double> animation;
  const _DotsAnimation({required this.animation});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: animation,
      builder: (context, child) => Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(3, (i) {
          // Stagger the dots
          final stagger = (animation.value - i * 0.15).clamp(0.3, 1.0);
          return Container(
            margin: const EdgeInsets.symmetric(horizontal: 3),
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: stagger),
              shape: BoxShape.circle,
            ),
          );
        }),
      ),
    );
  }
}
