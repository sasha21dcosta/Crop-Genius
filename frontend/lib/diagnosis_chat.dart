import 'package:flutter/material.dart';
import 'auth_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

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

  @override
  void initState() {
    super.initState();
    _loadUserCrops();
  }

  Future<void> _loadUserCrops() async {
    try {
      final token = await getToken();
      if (token == null) {
        setState(() => _cropsLoaded = true);
        return;
      }
      
      final response = await http.get(
        Uri.parse('$baseUrl/api/user/profile/'),
        headers: {'Authorization': 'Token $token'},
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _userCrops = List<String>.from(data['crops_list'] ?? []);
          _cropsLoaded = true;
        });
      } else {
        print('Error loading profile: ${response.statusCode} ${response.body}');
        setState(() => _cropsLoaded = true);
      }
    } catch (e) {
      print('Error loading user crops: $e');
      setState(() => _cropsLoaded = true);
    }
  }

  Future<void> _sendMessage({String? followupChoice}) async {
    final text = followupChoice == null ? _controller.text.trim() : _lastSymptomText ?? '';
    if (text.isEmpty || _selectedCrop == null) return;
    setState(() {
      if (followupChoice == null) {
        _messages.add(_ChatMessage(text, true));
        _lastSymptomText = text;
      } else {
        _messages.add(_ChatMessage('My answer: $followupChoice', true));
      }
      _loading = true;
      _controller.clear();
      _pendingFollowupQuestions = null;
    });
    await Future.delayed(const Duration(milliseconds: 100));
    _scrollToBottom();
    try {
      final body = followupChoice == null
          ? {'symptom_text': text, 'crop': _selectedCrop}
          : {'symptom_text': text, 'crop': _selectedCrop, 'followup_choice': followupChoice};
      final response = await http.post(
        Uri.parse('$baseUrl/api/disease/detect_disease/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['need_followup'] == true && data['followup_questions'] != null) {
          setState(() {
            _pendingFollowupQuestions = List<String>.from(data['followup_questions']);
            _messages.add(_ChatMessage(data['message'] ?? 'Please answer a follow-up question.', false));
          });
        } else if (data['final_prediction'] != null) {
          final pred = data['final_prediction'];
          final aiMsg =
              'Disease: ${pred['disease_name'] ?? ''}\nCrop: ${pred['crop'] ?? ''}\nMatched Symptom: ${pred['matched_symptom'] ?? ''}\nTreatment: ${pred['treatment'] ?? ''}\nPrevention: ${pred['prevention'] ?? ''}\nConfidence: ${(pred['confidence'] * 100).toStringAsFixed(1)}%';
          setState(() {
            _messages.add(_ChatMessage(aiMsg, false));
            _pendingFollowupQuestions = null;
          });
        } else {
          setState(() {
            _messages.add(_ChatMessage('No diagnosis result.', false));
          });
        }
      } else {
        setState(() {
          _messages.add(_ChatMessage('Error: ${response.statusCode}', false));
        });
      }
    } catch (e) {
      setState(() {
        _messages.add(_ChatMessage('Error: $e', false));
      });
    } finally {
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


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Disease Diagnosis'),
        backgroundColor: Colors.green.shade700,
      ),
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
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _controller,
                          decoration: InputDecoration(
                            hintText: _selectedCrop == null 
                                ? 'Select a crop first...' 
                                : 'Type symptoms for $_selectedCrop...',
                            enabled: _selectedCrop != null,
                          ),
                          onSubmitted: (_) => _sendMessage(),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.send, color: Colors.green),
                        onPressed: (_loading || _selectedCrop == null) ? null : _sendMessage,
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
  _ChatMessage(this.text, this.isUser);
}
