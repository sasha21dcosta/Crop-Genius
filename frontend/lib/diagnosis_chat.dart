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
  bool _awaitingFollowup = false;
  int? _lastFollowupIndex;

  Future<void> _sendMessage({String? followupChoice}) async {
    final text = followupChoice == null ? _controller.text.trim() : _lastSymptomText ?? '';
    if (text.isEmpty) return;
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
      _awaitingFollowup = false;
      _lastFollowupIndex = null;
    });
    await Future.delayed(const Duration(milliseconds: 100));
    _scrollToBottom();
    try {
      final body = followupChoice == null
          ? {'symptom_text': text}
          : {'symptom_text': text, 'followup_choice': followupChoice};
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
            _awaitingFollowup = true;
            _messages.add(_ChatMessage(data['message'] ?? 'Please answer a follow-up question.', false));
          });
        } else if (data['final_prediction'] != null) {
          final pred = data['final_prediction'];
          final aiMsg =
              'Disease: ${pred['disease_name'] ?? ''}\nCrop: ${pred['crop'] ?? ''}\nMatched Symptom: ${pred['matched_symptom'] ?? ''}\nTreatment: ${pred['treatment'] ?? ''}\nPrevention: ${pred['prevention'] ?? ''}\nConfidence: ${(pred['confidence'] * 100).toStringAsFixed(1)}%';
          setState(() {
            _messages.add(_ChatMessage(aiMsg, false));
            _pendingFollowupQuestions = null;
            _awaitingFollowup = false;
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

  Widget _buildCandidateSummary(List candidates) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 8),
        const Text('Possible Diseases (ranked):', style: TextStyle(fontWeight: FontWeight.bold)),
        ...candidates.asMap().entries.map((entry) {
          final i = entry.key;
          final c = entry.value;
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 4),
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${i + 1}. ${c['disease_name']} (Crop: ${c['crop']})', style: const TextStyle(fontWeight: FontWeight.bold)),
                  Text('Confidence: ${(c['avg_score'] * 100).toStringAsFixed(1)}%'),
                  Text('Symptoms: ${c['symptoms'].join(", ")}'),
                  Text('Treatments: ${c['treatments'].join(", ")}'),
                  Text('Preventions: ${c['preventions'].join(", ")}'),
                ],
              ),
            ),
          );
        }).toList(),
      ],
    );
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
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      decoration: const InputDecoration(
                        hintText: 'Type symptoms...'
                      ),
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.send, color: Colors.green),
                    onPressed: _loading ? null : _sendMessage,
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
  final List<dynamic>? candidates;
  _ChatMessage(this.text, this.isUser, {this.candidates});
}
