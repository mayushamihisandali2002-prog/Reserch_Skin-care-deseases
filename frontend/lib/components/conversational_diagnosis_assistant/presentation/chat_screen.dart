import 'dart:async';
import 'package:app/components/conversational_diagnosis_assistant/data/chat_api.dart';
import 'package:app/utils/app_styles.dart';
import 'package:flutter/material.dart';

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

  double _contentMaxWidth(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    if (width >= 1400) return 1160;
    if (width >= 1000) return 940;
    return width;
  }

  Widget _constrainedPane(BuildContext context, Widget child) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: _contentMaxWidth(context)),
        child: child,
      ),
    );
  }

  bool get _showStarterPrompts =>
      !_isTyping &&
      _messages.length == 1 &&
      _messages.first.sender == MessageSender.bot;

  static const List<String> _starterPrompts = [
    'I have acne and redness on my cheeks.',
    'Suggest a simple routine for dry skin.',
    'My skin is itchy and flaky. What could it be?',
    'How can I reduce dark spots safely?',
  ];

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
      final response = await ChatApi.sendMessage(text);
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
    return Scaffold(
      extendBodyBehindAppBar: true,
      backgroundColor: Colors.transparent,
      body: GestureDetector(
        onTap: () => FocusScope.of(context).unfocus(),
        child: Container(
          decoration: BoxDecoration(gradient: AppGradients.page(context)),
          child: Column(
            children: [
              _buildHeader(),
              Expanded(
                child: _constrainedPane(
                  context,
                  Stack(
                    children: [
                      _buildMessageList(),
                      if (_lastDisease != null)
                        Positioned(
                          top: 10,
                          left: 16,
                          right: 16,
                          child: _buildDiagnosisBanner(),
                        ),
                    ],
                  ),
                ),
              ),
              if (_isTyping)
                _constrainedPane(context, _buildTypingIndicator()),
              if (!_isConnected)
                _constrainedPane(context, _buildOfflineBanner()),
              _buildInputBar(),
            ],
          ),
        ),
      ),
    );
  }

  //
  Widget _buildHeader() {
    return ClipRRect(
      child: Container(
        padding: EdgeInsets.only(top: MediaQuery.of(context).padding.top),
        decoration: BoxDecoration(
          color: AppColors.primary.withValues(alpha: 0.85),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.1),
              blurRadius: 20,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: _constrainedPane(
          context,
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 10, 10, 16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.auto_awesome_rounded,
                    color: Colors.white,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Skin Health AI',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w800,
                          fontSize: 18,
                          letterSpacing: -0.5,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: Color(0xFF4ADE80),
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            'Online & Learning',
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.8),
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.delete_sweep_rounded, color: Colors.white70),
                  onPressed: _clearChat,
                ),
              ],
            ),
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
      itemCount: _messages.length + (_showStarterPrompts ? 1 : 0),
      itemBuilder: (_, i) {
        if (i < _messages.length) {
          return _buildMessageItem(_messages[i]);
        }
        return _buildStarterPrompts();
      },
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
              color: context.clrSurface.withValues(alpha: 0.98),
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
    final hasContent = _controller.text.trim().isNotEmpty;

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      decoration: BoxDecoration(
        color: context.clrSurface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 20,
            offset: const Offset(0, -5),
          ),
        ],
      ),
      child: _constrainedPane(
        context,
        Row(
          children: [
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(
                  color: context.clrBackground,
                  borderRadius: BorderRadius.circular(30),
                ),
                child: TextField(
                  controller: _controller,
                  focusNode: _focusNode,
                  maxLines: 4,
                  minLines: 1,
                  decoration: InputDecoration(
                    hintText: _followupPlaceholder ?? 'Describe symptoms...',
                    border: InputBorder.none,
                    hintStyle: AppTextStyles.caption(context).copyWith(fontSize: 15),
                  ),
                  onChanged: (_) => setState(() {}),
                ),
              ),
            ),
            const SizedBox(width: 12),
            GestureDetector(
              onTap: _isTyping || !hasContent ? null : () => _sendMessage(),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  gradient: hasContent ? AppGradients.premium : null,
                  color: hasContent ? null : (context.isDarkMode ? Colors.grey[800] : Colors.grey[200]),
                  shape: BoxShape.circle,
                  boxShadow: hasContent ? [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.3),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    )
                  ] : null,
                ),
                child: Icon(
                  _isTyping ? Icons.hourglass_empty_rounded : Icons.send_rounded,
                  color: hasContent ? Colors.white : Colors.grey[400],
                  size: 22,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStarterPrompts() {
    return Container(
      margin: const EdgeInsets.fromLTRB(44, 4, 44, 18),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: context.clrSurface.withValues(alpha: 0.9),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: context.clrBorder.withValues(alpha: 0.5)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 16,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Start with one of these',
            style: AppTextStyles.bodyStrong(context).copyWith(fontSize: 15),
          ),
          const SizedBox(height: 6),
          Text(
            'The assistant works best when you describe symptoms, body area, duration, and anything that makes it worse or better.',
            style: AppTextStyles.caption(context).copyWith(height: 1.45),
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: _starterPrompts
                .map(
                  (prompt) => InkWell(
                    onTap: () => _sendMessage(override: prompt),
                    borderRadius: BorderRadius.circular(22),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 12,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(22),
                        border: Border.all(
                          color: AppColors.primary.withValues(alpha: 0.15),
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.arrow_outward_rounded,
                            size: 16,
                            color: AppColors.primary,
                          ),
                          const SizedBox(width: 8),
                          ConstrainedBox(
                            constraints: const BoxConstraints(maxWidth: 260),
                            child: Text(
                              prompt,
                              style: AppTextStyles.body(context).copyWith(
                                color: AppColors.primaryDark,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                )
                .toList(),
          ),
        ],
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
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 620),
        child: Container(
          margin: const EdgeInsets.only(bottom: 16, left: 64),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          decoration: BoxDecoration(
            gradient: AppGradients.premium,
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(24),
              topRight: Radius.circular(24),
              bottomLeft: Radius.circular(24),
              bottomRight: Radius.circular(8),
            ),
            boxShadow: [
              BoxShadow(
                color: AppColors.primary.withValues(alpha: 0.2),
                blurRadius: 12,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: Text(
            message.text,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              height: 1.4,
              fontWeight: FontWeight.w500,
            ),
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
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 720),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      //
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: context.clrSurface.withValues(alpha: 0.96),
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
                          style: TextStyle(
                            fontSize: 10,
                            color: Colors.grey[400],
                          ),
                        ),
                      ),
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
            color: context.clrTextMain,
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
        color: context.isDarkMode ? const Color(0xFF064E3B) : const Color(0xFFF0FDF4),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: context.isDarkMode ? const Color(0xFF047857) : const Color(0xFF86EFAC)),
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
                Expanded(
                  child: Text(
                    'Treatment Options',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 13,
                      color: context.isDarkMode ? const Color(0xFF6EE7B7) : const Color(0xFF15803D),
                    ),
                  ),
                ),
                GestureDetector(
                  onTap: onToggle,
                  child: Row(
                    children: [
                      Text(
                        expanded ? 'Less' : 'All ${treatments.length}',
                        style: TextStyle(
                          fontSize: 11,
                          color: context.isDarkMode ? const Color(0xFF34D399) : const Color(0xFF16A34A),
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
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: context.isDarkMode ? const Color(0xFFA7F3D0) : const Color(0xFF166534),
                          ),
                        ),
                        if (advice.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 2),
                            child: Text(
                              advice,
                                style: TextStyle(
                                  fontSize: 11,
                                  color: context.isDarkMode ? Colors.grey[400] : Colors.grey[600],
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
                  color: context.clrSurface,
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
