import 'package:flutter/material.dart';
import 'auth_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';

class DiagnosisChatScreen extends StatefulWidget {
  const DiagnosisChatScreen({Key? key}) : super(key: key);

  @override
  State<DiagnosisChatScreen> createState() => _DiagnosisChatScreenState();
}

class _DiagnosisChatScreenState extends State<DiagnosisChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final List<_ChatMessage> _messages = [];
  bool _loading = false;
  final ScrollController _scrollController = ScrollController();
  String? _lastSymptomText;
  List<String>? _pendingFollowupQuestions;
  String? _selectedCrop;
  List<String> _userCrops = [];
  bool _cropsLoaded = false;
  String? _transcriptPreview;

  // Chat session management
  int? _currentSessionId;
  List<Map<String, dynamic>> _chatSessions = [];
  bool _sessionsLoaded = false;
  
  // Conversational state
  String? _currentDisease;
  List<Map<String, dynamic>>? _currentQuickActions;
  bool _isInClarificationMode = false;  // Track if we're in symptom selection mode

  @override
  void initState() {
    super.initState();
    _loadUserCrops();
    _loadChatSessions();
  }

  Future<void> _loadUserCrops() async {
    try {
      final token = await getToken();
      print('DEBUG - Token retrieved: ${token != null ? "Yes (${token.substring(0, 10)}...)" : "No token found"}');
      
      if (token == null) {
        print('DEBUG - No token found, crops cannot be loaded');
        setState(() => _cropsLoaded = true);
        return;
      }
      
      print('DEBUG - Calling user profile API...');
      final response = await http.get(
        Uri.parse('$baseUrl/api/user/profile/'),
        headers: {'Authorization': 'Token $token'},
      );
      
      print('DEBUG - Profile API response: ${response.statusCode}');
      print('DEBUG - Profile API body: ${response.body}');
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final cropsList = List<String>.from(data['crops_list'] ?? []);
        print('DEBUG - Crops loaded: $cropsList');
        setState(() {
          _userCrops = cropsList;
          _cropsLoaded = true;
        });
      } else {
        print('ERROR - Loading profile failed: ${response.statusCode} ${response.body}');
        setState(() => _cropsLoaded = true);
      }
    } catch (e) {
      print('ERROR - Exception loading user crops: $e');
      setState(() => _cropsLoaded = true);
    }
  }

  Future<void> _loadChatSessions() async {
    try {
      final token = await getToken();
      if (token == null) {
        setState(() => _sessionsLoaded = true);
        return;
      }

      final response = await http.get(
        Uri.parse('$baseUrl/api/disease/chat-sessions/'),
        headers: {'Authorization': 'Token $token'},
      );

      if (response.statusCode == 200) {
        final List<dynamic> sessions = jsonDecode(response.body);
        setState(() {
          _chatSessions = sessions.cast<Map<String, dynamic>>();
          _sessionsLoaded = true;
        });
        print('Loaded ${_chatSessions.length} chat sessions');
      } else {
        print('ERROR - Loading sessions failed: ${response.statusCode}');
        setState(() => _sessionsLoaded = true);
      }
    } catch (e) {
      print('ERROR - Exception loading sessions: $e');
      setState(() => _sessionsLoaded = true);
    }
  }

  Future<void> _createNewSession({bool closeDrawer = true}) async {
    if (_selectedCrop == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please select a crop first')),
        );
      }
      return;
    }

    try {
      final token = await getToken();
      if (token == null) return;

      final response = await http.post(
        Uri.parse('$baseUrl/api/disease/chat-sessions/'),
        headers: {
          'Authorization': 'Token $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({'crop': _selectedCrop}),
      );

      if (response.statusCode == 201) {
        final session = jsonDecode(response.body);
        if (!mounted) return;
        setState(() {
          _currentSessionId = session['id'];
          _messages.clear();
          _pendingFollowupQuestions = null;
        });
        await _loadChatSessions(); // Refresh session list
        print('Created new session: ${session['id']}');
        
        // Only close drawer if explicitly requested (when opened from drawer button)
        if (closeDrawer && mounted) {
          Navigator.pop(context);
        }
      }
    } catch (e) {
      print('ERROR - Creating session: $e');
    }
  }

  Future<void> _loadSession(int sessionId) async {
    try {
      final token = await getToken();
      if (token == null) return;

      final response = await http.get(
        Uri.parse('$baseUrl/api/disease/chat-sessions/$sessionId/'),
        headers: {'Authorization': 'Token $token'},
      );

      if (response.statusCode == 200) {
        final session = jsonDecode(response.body);
        setState(() {
          _currentSessionId = sessionId;
          _selectedCrop = session['crop'];
          _messages.clear();
          for (var msg in session['messages']) {
            _messages.add(_ChatMessage(msg['text'], msg['is_user'], metadata: msg['metadata']));
          }
        });
        print('Loaded session $sessionId with ${_messages.length} messages');
        Navigator.pop(context); // Close drawer
        _scrollToBottom();
      }
    } catch (e) {
      print('ERROR - Loading session: $e');
    }
  }

  Future<void> _saveMessage(String text, bool isUser, {Map<String, dynamic>? metadata}) async {
    if (_currentSessionId == null) return;

    try {
      final token = await getToken();
      if (token == null) return;

      await http.post(
        Uri.parse('$baseUrl/api/disease/chat-sessions/$_currentSessionId/messages/'),
        headers: {
          'Authorization': 'Token $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'text': text,
          'is_user': isUser,
          'metadata': metadata,
        }),
      );
    } catch (e) {
      print('ERROR - Saving message: $e');
    }
  }

  Future<void> _deleteSession(int sessionId) async {
    try {
      final token = await getToken();
      if (token == null) return;

      await http.delete(
        Uri.parse('$baseUrl/api/disease/chat-sessions/$sessionId/'),
        headers: {'Authorization': 'Token $token'},
      );

      setState(() {
        _chatSessions.removeWhere((s) => s['id'] == sessionId);
        if (_currentSessionId == sessionId) {
          _currentSessionId = null;
          _messages.clear();
        }
      });
    } catch (e) {
      print('ERROR - Deleting session: $e');
    }
  }

  Future<void> _sendSymptomSelection(String followupChoice) async {
    // User selected a symptom from clarification questions
    if (!mounted) return;
    
    final selectedSymptom = _pendingFollowupQuestions![int.parse(followupChoice)];
    
    setState(() {
      _messages.add(_ChatMessage('[Selected: $selectedSymptom]', true));
      _loading = true;
      _pendingFollowupQuestions = null;
    });
    
    await _saveMessage('[Selected: $selectedSymptom]', true);
    
    await Future.delayed(const Duration(milliseconds: 100));
    _scrollToBottom();
    
    try {
      final body = {
        'symptom_text': _lastSymptomText ?? '',
        'crop': _selectedCrop,
        'followup_answer': followupChoice,  // Send the selected index
      };
      
      final response = await http.post(
        Uri.parse('$baseUrl/api/disease/detect_disease/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      );
      
      if (!mounted) return;
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // Should receive confirmed diagnosis now
        if (data['type'] == 'diagnosis') {
          final aiMsg = data['message'] ?? 'Diagnosis complete.';
          final quickActions = data['quick_actions'] as List?;
          
          // Store disease name
          if (data['disease_identified'] != null) {
            _currentDisease = data['disease_identified']['disease_name'];
          }
          
          if (!mounted) return;
          setState(() {
            _messages.add(_ChatMessage(aiMsg, false, metadata: data));
            _pendingFollowupQuestions = null;
            _isInClarificationMode = false;
          });
          
          await _saveMessage(aiMsg, false, metadata: data);
          
          // Show conversational action buttons
          if (quickActions != null && quickActions.isNotEmpty) {
            final actionLabels = quickActions.map((a) => a['label'].toString()).toList();
            _currentQuickActions = quickActions.cast<Map<String, dynamic>>();
            if (!mounted) return;
            setState(() {
              _pendingFollowupQuestions = actionLabels;
            });
          }
        }
      } else {
        final aiMsg = 'Error: ${response.statusCode}';
        if (!mounted) return;
        setState(() {
          _messages.add(_ChatMessage(aiMsg, false));
        });
        await _saveMessage(aiMsg, false);
      }
    } catch (e) {
      final aiMsg = 'Error: $e';
      if (!mounted) return;
      setState(() {
        _messages.add(_ChatMessage(aiMsg, false));
      });
      await _saveMessage(aiMsg, false);
    } finally {
      if (!mounted) return;
      setState(() => _loading = false);
      _scrollToBottom();
    }
  }

  Future<void> _sendActionRequest(String action, String actionLabel) async {
    // Add user's choice as message
    if (!mounted) return;
    setState(() {
      _messages.add(_ChatMessage('[Selected: $actionLabel]', true));
      _loading = true;
      _pendingFollowupQuestions = null;
    });
    
    // Save user message
    await _saveMessage('[Selected: $actionLabel]', true);
    
    await Future.delayed(const Duration(milliseconds: 100));
    _scrollToBottom();
    
    try {
      final body = {
        'crop': _selectedCrop,
        'action': action,
        'disease_name': _currentDisease,
      };
      
      final response = await http.post(
        Uri.parse('$baseUrl/api/disease/detect_disease/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      );
      
      if (!mounted) return;
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        if (data['type'] == 'action_response' || data['type'] == 'conversation_end') {
          final aiMsg = data['message'] ?? 'Here you go!';
          final quickActions = data['quick_actions'] as List?;
          
          if (!mounted) return;
          setState(() {
            _messages.add(_ChatMessage(aiMsg, false, metadata: data));
            _pendingFollowupQuestions = null;
          });
          
          await _saveMessage(aiMsg, false, metadata: data);
          
          // Show new quick actions if available
          if (quickActions != null && quickActions.isNotEmpty) {
            final actionLabels = quickActions.map((a) => a['label'].toString()).toList();
            _currentQuickActions = quickActions.cast<Map<String, dynamic>>();
            if (!mounted) return;
            setState(() {
              _pendingFollowupQuestions = actionLabels;
            });
          }
        }
      } else {
        final aiMsg = 'Error: ${response.statusCode}';
        if (!mounted) return;
        setState(() {
          _messages.add(_ChatMessage(aiMsg, false));
        });
        await _saveMessage(aiMsg, false);
      }
    } catch (e) {
      final aiMsg = 'Error: $e';
      if (!mounted) return;
      setState(() {
        _messages.add(_ChatMessage(aiMsg, false));
      });
      await _saveMessage(aiMsg, false);
    } finally {
      if (!mounted) return;
      setState(() => _loading = false);
      _scrollToBottom();
    }
  }

  Future<void> _sendMessage({String? followupChoice}) async {
    // CASE 1: User clicked action button (Treatment, Prevention, etc.)
    if (followupChoice != null && _currentQuickActions != null && !_isInClarificationMode) {
      try {
        final actionIndex = int.parse(followupChoice);
        if (actionIndex >= 0 && actionIndex < (_pendingFollowupQuestions?.length ?? 0)) {
          final actionLabel = _pendingFollowupQuestions![actionIndex];
          final action = _currentQuickActions!.firstWhere(
            (a) => a['label'] == actionLabel,
            orElse: () => <String, dynamic>{},
          );
          
          if (action.isNotEmpty && _currentDisease != null) {
            await _sendActionRequest(action['action'], actionLabel);
            return;
          }
        }
      } catch (e) {
        print('Error parsing action: $e');
      }
    }
    
    // CASE 2: User selected a symptom from clarification questions
    if (followupChoice != null && _isInClarificationMode) {
      await _sendSymptomSelection(followupChoice);
      return;
    }
    
    // CASE 3: Regular symptom input (initial diagnosis)
    final text = followupChoice == null ? _controller.text.trim() : _lastSymptomText ?? '';
    if (text.isEmpty || _selectedCrop == null) return;
    
    // Create session if none exists
    if (_currentSessionId == null) {
      await _createNewSession(closeDrawer: false);
      if (_currentSessionId == null) return;
    }
    
    final userMessage = text;
    if (!mounted) return;
    setState(() {
      _messages.add(_ChatMessage(userMessage, true));
        _lastSymptomText = text;
      _loading = true;
      _controller.clear();
      _pendingFollowupQuestions = null;
      _isInClarificationMode = false;
    });
    
    await _saveMessage(userMessage, true);
    
    await Future.delayed(const Duration(milliseconds: 100));
    _scrollToBottom();
    try {
      final body = {'symptom_text': text, 'crop': _selectedCrop};
      final response = await http.post(
        Uri.parse('$baseUrl/api/disease/detect_disease/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      );
      
      if (!mounted) return;
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // STAGE 1: Clarification needed (symptom selection)
        if (data['type'] == 'clarification_needed' && data['need_followup'] == true) {
          final aiMsg = data['message'] ?? 'Please select a symptom.';
          final symptoms = data['followup_questions'] as List?;
          
          if (!mounted) return;
          setState(() {
            _messages.add(_ChatMessage(aiMsg, false, metadata: data));
            _pendingFollowupQuestions = symptoms?.cast<String>() ?? [];
            _isInClarificationMode = true;  // Enable clarification mode
            _currentQuickActions = null;  // Clear action buttons
          });
          
          await _saveMessage(aiMsg, false, metadata: data);
        }
        // STAGE 2: Confirmed diagnosis with conversational actions
        else if (data['type'] == 'diagnosis') {
          final aiMsg = data['message'] ?? 'Analysis complete.';
          final quickActions = data['quick_actions'] as List?;
          
          // Store disease name for action requests
          if (data['disease_identified'] != null) {
            _currentDisease = data['disease_identified']['disease_name'];
          }
          
          if (!mounted) return;
          setState(() {
            _messages.add(_ChatMessage(aiMsg, false, metadata: data));
            _pendingFollowupQuestions = null;
            _isInClarificationMode = false;  // Exit clarification mode
          });
          
          await _saveMessage(aiMsg, false, metadata: data);
          
          // Show conversational action buttons
          if (quickActions != null && quickActions.isNotEmpty) {
            final actionLabels = quickActions.map((a) => a['label'].toString()).toList();
            _currentQuickActions = quickActions.cast<Map<String, dynamic>>();
            if (!mounted) return;
            setState(() {
              _pendingFollowupQuestions = actionLabels;
            });
          }
        }
        // STAGE 2: Action responses
        else if (data['type'] == 'action_response') {
          final aiMsg = data['message'] ?? 'Here you go!';
          final quickActions = data['quick_actions'] as List?;
          
          if (!mounted) return;
          setState(() {
            _messages.add(_ChatMessage(aiMsg, false, metadata: data));
            _pendingFollowupQuestions = null;
          });
          
          await _saveMessage(aiMsg, false, metadata: data);
          
          // Show next action options
          if (quickActions != null && quickActions.isNotEmpty) {
            final actionLabels = quickActions.map((a) => a['label'].toString()).toList();
            _currentQuickActions = quickActions.cast<Map<String, dynamic>>();
            if (!mounted) return;
          setState(() {
              _pendingFollowupQuestions = actionLabels;
            });
          }
        }
        // Conversation end
        else if (data['type'] == 'conversation_end') {
          final aiMsg = data['message'] ?? 'Conversation complete.';
          if (!mounted) return;
          setState(() {
            _messages.add(_ChatMessage(aiMsg, false));
            _pendingFollowupQuestions = null;
            _isInClarificationMode = false;
          });
          await _saveMessage(aiMsg, false);
        }
        else {
          final aiMsg = 'No diagnosis result.';
          if (!mounted) return;
          setState(() {
            _messages.add(_ChatMessage(aiMsg, false));
          });
          await _saveMessage(aiMsg, false);
        }
      } else {
        final aiMsg = 'Error: ${response.statusCode}';
        if (!mounted) return;
        setState(() {
          _messages.add(_ChatMessage(aiMsg, false));
        });
        await _saveMessage(aiMsg, false);
      }
    } catch (e) {
      final aiMsg = 'Error: $e';
      if (!mounted) return;
      setState(() {
        _messages.add(_ChatMessage(aiMsg, false));
      });
      await _saveMessage(aiMsg, false);
    } finally {
      if (!mounted) return;
      setState(() => _loading = false);
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Widget _buildChatDrawer() {
    return Drawer(
      child: Column(
        children: [
          // Drawer Header
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.green.shade700, Colors.green.shade500],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: SafeArea(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Icon(Icons.eco, size: 40, color: Colors.white),
                  SizedBox(height: 10),
                  Text(
                    'Chat History',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    'Disease Diagnosis Chats',
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          // New Chat Button
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _createNewSession,
                icon: const Icon(Icons.add),
                label: const Text('New Chat'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green.shade600,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
              ),
            ),
          ),
          
          // Session Count
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Recent Chats',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: Colors.grey.shade700,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green.shade100,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${_chatSessions.length}/3',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.green.shade800,
                    ),
                  ),
                ),
              ],
            ),
          ),
          
          const Divider(),
          
          // Chat Sessions List
          Expanded(
            child: _chatSessions.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.chat_bubble_outline, size: 60, color: Colors.grey.shade300),
                        const SizedBox(height: 16),
                        Text(
                          'No chat history yet',
                          style: TextStyle(color: Colors.grey.shade600, fontSize: 16),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Start a new conversation',
                          style: TextStyle(color: Colors.grey.shade400, fontSize: 14),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    itemCount: _chatSessions.length,
                    itemBuilder: (context, index) {
                      final session = _chatSessions[index];
                      final isActive = session['id'] == _currentSessionId;
                      return Card(
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        elevation: isActive ? 4 : 1,
                        color: isActive ? Colors.green.shade50 : Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: isActive
                              ? BorderSide(color: Colors.green.shade300, width: 2)
                              : BorderSide.none,
                        ),
                        child: ListTile(
                          leading: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: isActive ? Colors.green.shade200 : Colors.green.shade50,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Icon(
                              Icons.chat_bubble,
                              color: Colors.green.shade700,
                              size: 20,
                            ),
                          ),
                          title: Text(
                            session['title'] ?? session['preview'] ?? 'Chat ${session['id']}',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
                            ),
                          ),
                          subtitle: Text(
                            '${session['crop'].toString().toUpperCase()} • ${session['message_count']} messages',
                            style: const TextStyle(fontSize: 12),
                          ),
                          trailing: IconButton(
                            icon: const Icon(Icons.delete_outline, size: 20),
                            color: Colors.red.shade400,
                            onPressed: () => _deleteSession(session['id']),
                          ),
                          onTap: () => _loadSession(session['id']),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('AI Disease Diagnosis'),
            if (_currentSessionId != null)
              Text(
                '${_selectedCrop?.toUpperCase() ?? "CHAT"}',
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w300),
              ),
          ],
        ),
        backgroundColor: Colors.green.shade700,
      ),
      drawer: _buildChatDrawer(),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(12),
              itemCount: _messages.length + (_pendingFollowupQuestions != null ? 1 : 0),
              itemBuilder: (context, idx) {
                if (_pendingFollowupQuestions != null && idx == _messages.length) {
                  // Show follow-up options
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 8),
                      ...List.generate(_pendingFollowupQuestions!.length, (i) => Padding(
                        padding: const EdgeInsets.symmetric(vertical: 2),
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green.shade200,
                          ),
                          onPressed: _loading ? null : () => _sendMessage(followupChoice: (i).toString()),
                          child: Text('${i + 1}. ${_pendingFollowupQuestions![i]}'),
                        ),
                      )),
                    ],
                  );
                }
                final msg = _messages[idx];
                // Remove candidate summary cards
                // if (msg.candidates != null) {
                //   return _buildCandidateSummary(msg.candidates!);
                // }
                return Align(
                  alignment: msg.isUser
                      ? Alignment.centerRight
                      : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.symmetric(
                        vertical: 10, horizontal: 14),
                    decoration: BoxDecoration(
                      color: msg.isUser
                          ? Colors.green.shade100
                          : Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(msg.text),
                  ),
                );
              },
            ),
          ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: CircularProgressIndicator(),
            ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
              child: Column(
                children: [
                  // Crop selection dropdown
                  if (!_cropsLoaded)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          children: [
                            const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                            const SizedBox(width: 12),
                            Text('Loading your crops...', style: TextStyle(color: Colors.grey.shade600)),
                          ],
                        ),
                      ),
                    )
                  else if (_cropsLoaded)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: _userCrops.isNotEmpty
                          ? DropdownButtonFormField<String>(
                              value: _selectedCrop,
                              decoration: const InputDecoration(
                                labelText: 'Select Crop',
                                border: OutlineInputBorder(),
                              ),
                              items: _userCrops.map((crop) {
                                return DropdownMenuItem(
                                  value: crop,
                                  child: Text(crop.toUpperCase()),
                                );
                              }).toList(),
                              onChanged: (value) {
                                setState(() {
                                  _selectedCrop = value;
                                });
                              },
                            )
                          : Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: Colors.orange.shade50,
                                border: Border.all(color: Colors.orange.shade200),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Column(
                                children: [
                                  Icon(Icons.warning, color: Colors.orange.shade600),
                                  const SizedBox(height: 8),
                                  Text(
                                    'No crops found in your profile',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: Colors.orange.shade800,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Please register with crops first, or contact support.',
                                    style: TextStyle(color: Colors.orange.shade700),
                                    textAlign: TextAlign.center,
                                  ),
                                ],
                              ),
                            ),
                    ),
                  if (_transcriptPreview != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 13),
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: Colors.green.shade100, width: 1),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Flexible(
                              child: Text(_transcriptPreview!, style: const TextStyle(fontSize: 15, color: Colors.black, fontWeight: FontWeight.w500)),
                            ),
                            IconButton(
                              icon: const Icon(Icons.clear, size: 18, color: Colors.red),
                              onPressed: () => setState(() => _transcriptPreview = null),
                              tooltip: 'Clear transcript',
                            )
                          ],
                        ),
                      ),
                    ),
                  Row(
                    children: [
                      SpeechToTextMic(
                        onTranscript: (t) => setState(() {
                          _transcriptPreview = t;
                          _controller.text = t;
                          _controller.selection = TextSelection.collapsed(offset: t.length);
                        }),
                        enabled: _selectedCrop != null && !_loading,
                      ),
                      Expanded(
                        child: TextField(
                          controller: _controller,
                          decoration: InputDecoration(
                            hintText: _selectedCrop == null
                                ? 'कृपया पहले फसल चुने... | कृपया योग्य पीक निवडा... | Select a crop first...'
                                : 'लक्षण टाइप कीजिये या बोलिए... | लक्षण बोला किंवा टाइप करा... | Type or speak symptoms for $_selectedCrop...',
                            enabled: _selectedCrop != null,
                          ),
                          onSubmitted: (_) => _sendMessage(),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.send, color: Colors.green),
                        onPressed: (_loading || _selectedCrop == null)
                            ? null
                            : () {
                                setState(() => _transcriptPreview = null);
                                _sendMessage();
                              },
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ChatMessage {
  final String text;
  final bool isUser;
  final Map<String, dynamic>? metadata;
  _ChatMessage(this.text, this.isUser, {this.metadata});
}

class SpeechToTextMic extends StatefulWidget {
  final Function(String transcript) onTranscript;
  final bool enabled;
  const SpeechToTextMic({Key? key, required this.onTranscript, required this.enabled}) : super(key: key);
  @override
  State<SpeechToTextMic> createState() => _SpeechToTextMicState();
}

class _SpeechToTextMicState extends State<SpeechToTextMic> {
  bool _isRecording = false;
  bool _isLoading = false;
  String? _errorMsg;
  final AudioRecorder _recorder = AudioRecorder();

  Future<void> _start() async {
    _errorMsg = null;
    final perm = await Permission.microphone.request();
    if (!perm.isGranted) {
      setState(() => _errorMsg = 'Microphone permission denied');
      return;
    }
    try {
      final dir = await getTemporaryDirectory();
      final outPath = "${dir.path}/audio_${DateTime.now().millisecondsSinceEpoch}.wav";
      await _recorder.start(
        const RecordConfig(
          encoder: AudioEncoder.wav,
          bitRate: 128000,
          sampleRate: 16000,
        ),
        path: outPath,
      );
      setState(() => _isRecording = true);
    } catch (e) {
      setState(() => _errorMsg = 'Unable to start recording: $e');
    }
  }

  Future<void> _stopAndSend() async {
    setState(() {
      _isRecording = false;
      _isLoading = true;
    });
    try {
      final path = await _recorder.stop();
      if (path == null) {
        setState(() { _isLoading = false; _errorMsg = 'No audio detected.'; });
        return;
      }
      final file = File(path);
      final url = Uri.parse("$baseUrl/api/disease/transcribe_audio/");
      final req = http.MultipartRequest('POST', url)
        ..files.add(await http.MultipartFile.fromPath('audio', file.path));
      final resp = await req.send();
      final body = await resp.stream.bytesToString();
      if (resp.statusCode == 200) {
        final json = jsonDecode(body);
        String? transcript = json['transcript']?.trim();
        String? originalTranscript = json['original_transcript']?.trim();
        String? detectedLanguage = json['detected_language'];
        bool translationApplied = json['translation_applied'] ?? false;
        
        print('===== TRANSCRIPTION RESULTS =====');
        print('Original (Whisper): $originalTranscript');
        print('Translated (Ollama): $transcript');
        print('Language: $detectedLanguage');
        print('Translation applied: $translationApplied');
        print('=================================');
        
        if (transcript == null || transcript.isEmpty) {
          setState(() {
            _errorMsg = 'Speech not recognized. Please speak closer and clearly.';
            _isLoading = false;
          });
        } else {
          widget.onTranscript(transcript);
          setState(() {
            _errorMsg = null;
            _isLoading = false;
          });
        }
      } else {
        final error = jsonDecode(body)['error'] ?? 'Speech-to-text failed. Try again.';
        setState(() { _errorMsg = error; _isLoading = false; });
      }
    } catch (e) {
      setState(() { _errorMsg = 'Audio upload failed. Check your network.'; _isLoading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconButton(
          icon: Icon(_isRecording ? Icons.stop_circle : Icons.mic, color: widget.enabled ? Colors.green.shade800 : Colors.grey),
          onPressed: widget.enabled && !_isLoading
            ? () {
                if (_isRecording) {
                  _stopAndSend();
                } else {
                  _start();
                }
              }
            : null,
          tooltip: _isRecording ? 'Stop Recording' : 'Speak Symptoms',
        ),
        if (_isLoading)
          const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
        if (_errorMsg != null)
          Padding(
            padding: const EdgeInsets.only(left: 8),
            child: Text(_errorMsg!, style: const TextStyle(color: Colors.red, fontSize: 12)),
          ),
      ],
    );
  }
}
