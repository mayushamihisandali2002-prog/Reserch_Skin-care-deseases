import 'dart:async';
import 'package:app/services/api_service.dart';
import 'package:app/services/supabase_service.dart';
import 'package:app/utils/app_styles.dart';
import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

//
// DATA MODELS
//

enum MessageSender { user, bot }

class ChatMessage {
  final MessageSender sender;
  final String text;
  final Map<String, dynamic>? apiResponse;
  final DateTime timestamp;

  const ChatMessage({
    required this.sender,
    required this.text,
    this.apiResponse,
    required this.timestamp,
  });
}

class ChatSession {
  final String id;
  final String title;
  final DateTime updatedAt;

  ChatSession({
    required this.id,
    required this.title,
    required this.updatedAt,
  });

  factory ChatSession.fromJson(Map<String, dynamic> json) {
    return ChatSession(
      id: json['id'] as String,
      title: json['title'] as String? ?? 'New Conversation',
      updatedAt: DateTime.parse(json['created_at'] as String), // or updated_at
    );
  }
}

//
// SCREEN
//

class ChatScreen extends StatefulWidget {
  final String? initialMessage;
  const ChatScreen({super.key, this.initialMessage});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with TickerProviderStateMixin {
  final List<ChatMessage> _messages = [];
  List<ChatSession> _sessions = [];
  String? _currentSessionId;
  bool _isLoadingSessions = false;
  bool _isInitialLoad = true;

  final TextEditingController _controller = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  final ScrollController _scrollController = ScrollController();

  bool _isTyping = false;
  bool _isConnected = true;
  String? _lastDisease;

  late AnimationController _dotController;
  late Animation<double> _dotAnimation;

  @override
  void initState() {
    super.initState();
    _currentSessionId = ApiService.sessionId;
    _dotController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);
    _dotAnimation = Tween<double>(begin: 0.3, end: 1.0).animate(_dotController);
    
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    await _loadSessions();
    if (!mounted) return;
    if (_sessions.isNotEmpty) {
      // Pick the most recent session automatically if current is empty?
      // For now, stick with the global sessionId if it has messages, or start fresh.
    }
    setState(() {
      _messages.add(
        ChatMessage(
          sender: MessageSender.bot,
          text: 'Hello! I\'m your SkinAI Assistant. I can help you identify skin conditions and provide care recommendations. How can I help you today?',
          timestamp: DateTime.now(),
        ),
      );
      _isInitialLoad = false;
    });

    if (widget.initialMessage != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _sendMessage(override: widget.initialMessage);
      });
    }
  }

  @override
  void dispose() {
    _dotController.dispose();
    _controller.dispose();
    _focusNode.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadSessions() async {
    final uid = SupabaseService.userId;
    if (uid == null || uid == 'anonymous') {
      // For guest users, we still want to show the current session in the sidebar
      if (mounted) {
        setState(() {
          if (_currentSessionId != null && !_sessions.any((s) => s.id == _currentSessionId)) {
            _sessions = [
              ChatSession(
                id: _currentSessionId!, 
                title: 'Current Consultation', 
                updatedAt: DateTime.now()
              )
            ];
          }
        });
      }
      return;
    }
    
    if (mounted) setState(() => _isLoadingSessions = true);
    try {
      final data = await ApiService.getChatSessions();
      if (mounted) {
        setState(() {
          _sessions = data.map((json) => ChatSession.fromJson(json)).toList();
          
          // Ensure current session is in the list even if DB hasn't updated yet
          if (_currentSessionId != null && !_sessions.any((s) => s.id == _currentSessionId)) {
            _sessions.insert(0, ChatSession(
              id: _currentSessionId!,
              title: 'Current Consultation',
              updatedAt: DateTime.now(),
            ));
          }
        });
      }
    } finally {
      if (mounted) setState(() => _isLoadingSessions = false);
    }
  }

  Future<void> _selectSession(String sid) async {
    if (_isTyping) return;
    
    setState(() {
      _currentSessionId = sid;
      _messages.clear();
      _isTyping = true;
      _lastDisease = null;
    });

    try {
      final history = await ApiService.getChatMessages(sid);
      if (mounted) {
        setState(() {
          for (var raw in history) {
            _messages.add(ChatMessage(
              sender: raw['sender'] == 'user' ? MessageSender.user : MessageSender.bot,
              text: raw['message'] ?? '',
              timestamp: DateTime.parse(raw['created_at']),
              apiResponse: raw,
            ));
            
            if (raw['sender'] == 'bot' && raw['predicted_disease'] != null) {
              _lastDisease = raw['predicted_disease'];
            }
          }
          _isTyping = false;
        });
        _scrollToBottom();
      }
    } catch (e) {
      if (mounted) setState(() => _isTyping = false);
    }
  }

  Future<void> _deleteSession(String sid) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Conversation?'),
        content: const Text('This will permanently delete this chat history.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(context, true), 
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    try {
      await ApiService.deleteChatSession(sid);
      if (_currentSessionId == sid) {
         _startNewChat();
      } else {
        _loadSessions();
      }
    } catch (e) {
      debugPrint("Delete failed: $e");
    }
  }

  void _startNewChat() {
    final newId = const Uuid().v4();
    ApiService.sessionId = newId;
    setState(() {
      _currentSessionId = newId;
      _messages.clear();
      _lastDisease = null;
      _messages.add(
        ChatMessage(
          sender: MessageSender.bot,
          text: 'New conversation started. Describe your symptoms or ask a question.',
          timestamp: DateTime.now(),
        ),
      );
    });
  }

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

  Future<void> _sendMessage({String? override}) async {
    final text = override ?? _controller.text.trim();
    if (text.isEmpty || _isTyping) return;

    final sid = _currentSessionId ?? ApiService.sessionId;

    setState(() {
      _messages.add(
        ChatMessage(
          sender: MessageSender.user,
          text: text,
          timestamp: DateTime.now(),
        ),
      );
      _isTyping = true;
    });
    
    // Clear the controller immediately for a snappier feel
    _controller.clear();
    _scrollToBottom();

    try {
      final response = await ApiService.sendChatMessage(text, customSessionId: sid);
      if (!mounted) return;

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
      
      // If the AI returned a chat title, update our local session title immediately
      final suggestedTitle = response['chat_title'] as String?;
      if (suggestedTitle != null) {
        setState(() {
          // Find the current session in our list and update its title
          final index = _sessions.indexWhere((s) => s.id == sid);
          if (index != -1) {
            _sessions[index] = ChatSession(
              id: sid,
              title: suggestedTitle,
              updatedAt: DateTime.now(),
            );
          } else {
            // If for some reason it's not in the list, add it
            _sessions.insert(0, ChatSession(
              id: sid,
              title: suggestedTitle,
              updatedAt: DateTime.now(),
            ));
          }
        });
      }

      // Also trigger a background load to sync with DB if logged in
      if (SupabaseService.userId != null && SupabaseService.userId != 'anonymous') {
        _loadSessions();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isConnected = false;
          _messages.add(
            ChatMessage(
              sender: MessageSender.bot,
              text: 'Could not connect. Please check your connection.',
              apiResponse: {'_error': true},
              timestamp: DateTime.now(),
            ),
          );
        });
      }
    } finally {
      if (mounted) {
        setState(() => _isTyping = false);
        _scrollToBottom();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDesktop = MediaQuery.of(context).size.width > 900;

    return Scaffold(
      drawer: isDesktop ? null : Drawer(child: _buildSidebar()),
      body: Row(
        children: [
          if (isDesktop) 
            SizedBox(width: 280, child: _buildSidebar()),
          Expanded(
            child: Container(
              color: context.isDarkMode ? const Color(0xFF0D1117) : const Color(0xFFFAFBFC),
              child: Column(
                children: [
                  _buildHeader(!isDesktop),
                  Expanded(
                    child: Stack(
                      children: [
                        _buildMessageList(),
                        if (_lastDisease != null)
                          Positioned(
                            top: 10,
                            left: 0,
                            right: 0,
                            child: _buildDiagnosisBanner(),
                          ),
                      ],
                    ),
                  ),
                  if (_isTyping) _buildTypingIndicator(),
                  _buildInputBar(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSidebar() {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF10252D), // Original deep clinical teal
        border: Border(right: BorderSide(color: Colors.white.withOpacity(0.1))),
      ),
      child: Column(
        children: [
          const SizedBox(height: 60),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: InkWell(
              onTap: _startNewChat,
              borderRadius: BorderRadius.circular(12),
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.white.withOpacity(0.1)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.add, color: Colors.white, size: 20),
                    const SizedBox(width: 12),
                    const Text('New Consultation', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text('CHAT HISTORY', style: TextStyle(color: Colors.white54, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
            ),
          ),
          Expanded(
            child: _isLoadingSessions 
              ? const Center(child: CircularProgressIndicator(color: Colors.white54))
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  itemCount: _sessions.length,
                  itemBuilder: (_, i) {
                    final s = _sessions[i];
                    final isSelected = s.id == _currentSessionId;
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 2),
                      child: ListTile(
                        dense: true,
                        selected: isSelected,
                        selectedTileColor: Colors.white.withOpacity(0.08),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        leading: Icon(Icons.chat_outlined, size: 16, color: isSelected ? Colors.white : Colors.white60),
                        title: Text(
                          s.title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 13,
                            color: isSelected ? Colors.white : Colors.white70,
                            fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                          ),
                        ),
                        trailing: isSelected 
                          ? IconButton(
                              icon: const Icon(Icons.delete_outline, size: 14, color: Colors.white54),
                              onPressed: () => _deleteSession(s.id),
                            ) 
                          : null,
                        onTap: () {
                          _selectSession(s.id);
                          if (MediaQuery.of(context).size.width <= 900) Navigator.pop(context);
                        },
                      ),
                    );
                  },
                ),
          ),
          _buildUserActionSection(),
        ],
      ),
    );
  }

  Widget _buildUserActionSection() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(border: Border(top: BorderSide(color: Colors.white.withOpacity(0.1)))),
      child: Row(
        children: [
          CircleAvatar(
            radius: 14,
            backgroundColor: Colors.white24,
            child: const Icon(Icons.person, size: 16, color: Colors.white),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              SupabaseService.currentUser?.userMetadata?['full_name'] ?? 'User Profile',
              style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(bool showMenu) {
    return Container(
      padding: EdgeInsets.fromLTRB(20, MediaQuery.of(context).padding.top + 10, 20, 16),
      decoration: BoxDecoration(
        color: context.isDarkMode ? const Color(0xFF161B22) : Colors.white,
        border: Border(bottom: BorderSide(color: context.clrBorder.withOpacity(0.1))),
      ),
      child: Row(
        children: [
          if (showMenu) IconButton(icon: const Icon(Icons.menu), onPressed: () => Scaffold.of(context).openDrawer()),
          const Icon(Icons.auto_awesome_rounded, color: AppColors.primary, size: 20),
          const SizedBox(width: 12),
          Text('Clinical Assistant', style: AppTextStyles.subHeading(context).copyWith(fontSize: 16)),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.delete_outline, size: 18),
            onPressed: () => setState(() => _messages.clear()),
          ),
        ],
      ),
    );
  }

  Widget _buildDiagnosisBanner() {
    return Center(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: AppColors.primary.withOpacity(0.1),
          borderRadius: BorderRadius.circular(30),
          border: Border.all(color: AppColors.primary.withOpacity(0.2)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.biotech, size: 16, color: AppColors.primary),
            const SizedBox(width: 8),
            Text('Analyzing: ', style: TextStyle(fontSize: 12, color: Colors.grey[700])),
            Text(_lastDisease!, style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary, fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageList() {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 800),
        child: ListView.builder(
          controller: _scrollController,
          padding: const EdgeInsets.fromLTRB(20, 30, 20, 10),
          itemCount: _messages.length,
          itemBuilder: (_, i) => _messages[i].sender == MessageSender.user 
            ? _UserBubble(message: _messages[i]) 
            : _BotBubble(message: _messages[i]),
        ),
      ),
    );
  }

  Widget _buildInputBar() {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 800),
        child: Container(
          margin: const EdgeInsets.fromLTRB(20, 0, 20, 30),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
          decoration: BoxDecoration(
            color: context.clrSurface,
            borderRadius: BorderRadius.circular(30),
            border: Border.all(color: context.clrBorder.withOpacity(0.3)),
            boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 15, offset: const Offset(0, 4))],
          ),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _controller,
                  focusNode: _focusNode,
                  decoration: const InputDecoration(hintText: 'Ask about a skin condition...', border: InputBorder.none),
                  onSubmitted: (_) => _sendMessage(),
                ),
              ),
              IconButton(icon: const Icon(Icons.send_rounded, color: AppColors.primary), onPressed: _sendMessage),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTypingIndicator() {
     return Center(child: Padding(padding: const EdgeInsets.all(20), child: _DotsAnimation(animation: _dotAnimation)));
  }
}

class _UserBubble extends StatelessWidget {
  final ChatMessage message;
  const _UserBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.only(bottom: 24, left: 100),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        decoration: BoxDecoration(
          gradient: AppGradients.premium,
          borderRadius: BorderRadius.circular(20).copyWith(bottomRight: Radius.zero),
        ),
        child: Text(message.text, style: const TextStyle(color: Colors.white, fontSize: 15, height: 1.45)),
      ),
    );
  }
}

class _BotBubble extends StatelessWidget {
  final ChatMessage message;
  const _BotBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 30, right: 100),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.auto_awesome, size: 14, color: AppColors.primary),
                const SizedBox(width: 8),
                Text('SkinAI Assistant', style: AppTextStyles.bodyStrong(context).copyWith(fontSize: 12, color: AppColors.primary)),
              ],
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16).copyWith(topLeft: Radius.circular(0)),
                border: Border.all(color: Colors.black.withOpacity(0.05)),
                boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 10, offset: const Offset(0, 2))],
              ),
              child: _RichBotText(text: message.text),
            ),
            Padding(
              padding: const EdgeInsets.only(top: 8, left: 4),
              child: Text(
                '${message.timestamp.hour}:${message.timestamp.minute.toString().padLeft(2, '0')}',
                style: TextStyle(fontSize: 10, color: Colors.grey[400]),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RichBotText extends StatelessWidget {
  final String text;
  const _RichBotText({required this.text});

  @override
  Widget build(BuildContext context) {
    return MarkdownBody(
      data: text,
      selectable: true,
      styleSheet: MarkdownStyleSheet(
        p: AppTextStyles.body(context).copyWith(height: 1.6, fontSize: 14),
        h3: AppTextStyles.subHeading(context).copyWith(color: AppColors.primary, fontSize: 18, fontWeight: FontWeight.bold),
        listBullet: const TextStyle(color: AppColors.primary),
        strong: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blueAccent),
      ),
    );
  }
}

class _DotsAnimation extends AnimatedWidget {
  const _DotsAnimation({required Animation<double> animation}) : super(listenable: animation);
  @override
  Widget build(BuildContext context) {
    final animation = listenable as Animation<double>;
    return Row(mainAxisSize: MainAxisSize.min, children: List.generate(3, (i) => Padding(padding: const EdgeInsets.symmetric(horizontal: 2), child: Opacity(opacity: animation.value, child: Container(width: 6, height: 6, decoration: const BoxDecoration(color: AppColors.primary, shape: BoxShape.circle))))));
  }
}

