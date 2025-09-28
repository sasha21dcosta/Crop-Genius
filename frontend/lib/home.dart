import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'marketplace.dart';
import 'auth_service.dart';
import 'diagnosis_chat.dart';
import 'package:url_launcher/url_launcher.dart';

class HomePage extends StatefulWidget {
  final String userName;
  const HomePage({Key? key, required this.userName}) : super(key: key);

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final TextEditingController _symptomController = TextEditingController();
  Map<String, dynamic>? _diagnosisResult;
  bool _loading = false;

  Future<void> _runDiagnosis() async {
    setState(() => _loading = true);
    final result = await detectDisease(_symptomController.text);
    setState(() {
      _diagnosisResult = result;
      _loading = false;
    });
  }

  Future<Map<String, dynamic>?> detectDisease(String symptomText) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/disease/detect_disease/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'symptom_text': symptomText}),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      print('Error:  [31m${response.statusCode} [0m');
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.green.shade50,
      appBar: AppBar(
        backgroundColor: Colors.green.shade700,
        title: const Text('AgroConnect  🌾'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications),
            tooltip: 'Owner Requests',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const OwnerRequestsPage()),
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            Image.network(
              'https://plus.unsplash.com/premium_photo-1661962692059-55d5a4319814?w=600&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8YWdyaWN1bHR1cmV8ZW58MHx8MHx8fDA%3D',
              height: 200,
              width: double.infinity,
              fit: BoxFit.cover,
            ),
            const SizedBox(height: 20),
            Text(
              'Welcome ${widget.userName}',
              style: TextStyle(
                fontSize: 26,
                fontWeight: FontWeight.bold,
                color: Colors.green.shade800,
              ),
            ),
            const SizedBox(height: 10),
            Text(
              'Empowering you with agriculture technology.',
              style: TextStyle(
                fontSize: 16,
                color: Colors.green.shade900,
              ),
            ),
            const SizedBox(height: 30),
            _featureCard(context, Icons.eco, 'Symptom Input AI diagnosis'),
            _featureCard(context, Icons.cloud, ' Crop Suggestions'),
            _featureCard(context, Icons.shopping_cart, 'Marketplace and Equipment Rental'),
            _featureCard(context, Icons.support, 'real-time crop prices'),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  void _showDiagnosisDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setState) {
            return AlertDialog(
              title: const Text('AI Disease Diagnosis'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(
                      controller: _symptomController,
                      decoration: const InputDecoration(
                        labelText: 'Enter or speak symptoms',
                        border: OutlineInputBorder(),
                      ),
                      minLines: 1,
                      maxLines: 3,
                    ),
                    const SizedBox(height: 10),
                    ElevatedButton.icon(
                      onPressed: _loading
                          ? null
                          : () async {
                              setState(() => _loading = true);
                              final result = await detectDisease(_symptomController.text);
                              setState(() {
                                _diagnosisResult = result;
                                _loading = false;
                              });
                            },
                      icon: const Icon(Icons.medical_services),
                      label: _loading ? const Text('Diagnosing...') : const Text('AI Diagnosis'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green.shade700,
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                      ),
                    ),
                    if (_diagnosisResult != null) ...[
                      const SizedBox(height: 20),
                      Card(
                        margin: EdgeInsets.zero,
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Disease: ${_diagnosisResult!['predicted_disease']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                              Text('Crop: ${_diagnosisResult!['crop']}'),
                              Text('Matched Symptom: ${_diagnosisResult!['matched_symptom']}'),
                              Text('Treatment: ${_diagnosisResult!['treatment']}'),
                              Text('Prevention: ${_diagnosisResult!['prevention']}'),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () {
                    Navigator.of(context).pop();
                    setState(() {
                      _diagnosisResult = null;
                      _symptomController.clear();
                    });
                  },
                  child: const Text('Close'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Widget _featureCard(BuildContext context, IconData icon, String title) {
    return Card(
      elevation: 4,
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: ListTile(
        leading: Icon(icon, color: Colors.green.shade700, size: 30),
        title: Text(title, style: TextStyle(fontSize: 18)),
        trailing: const Icon(Icons.arrow_forward_ios),
        onTap: () async {
          if (title == 'Symptom Input AI diagnosis') {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const DiagnosisChatScreen()),
            );
          } else if (title == 'Marketplace and Equipment Rental') {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const MarketplaceScreen()),
            );
          }
        },
      ),
    );
  }
}

class OwnerRequestsPage extends StatefulWidget {
  const OwnerRequestsPage({Key? key}) : super(key: key);

  @override
  State<OwnerRequestsPage> createState() => _OwnerRequestsPageState();
}

class _OwnerRequestsPageState extends State<OwnerRequestsPage> {
  late Future<List<dynamic>> _futureRequests;

  @override
  void initState() {
    super.initState();
    _futureRequests = fetchOwnerRequests();
  }

  Future<List<dynamic>> fetchOwnerRequests() async {
    final token = await getToken();
    print('OwnerRequestsPage: token=$token');
    final res = await http.get(
      Uri.parse('$baseUrl/api/bookings/owner/'),
      headers: {'Authorization': 'Token $token'},
    );
    print('OwnerRequestsPage: status=${res.statusCode}, body=${res.body}');
    if (res.statusCode == 200) {
      return jsonDecode(res.body) as List<dynamic>;
    }
    return [];
  }

  Future<void> _respondToRequest(int bookingId, String action) async {
    final token = await getToken();
    final res = await http.post(
      Uri.parse('$baseUrl/api/bookings/$bookingId/respond/'),
      headers: {'Authorization': 'Token $token', 'Content-Type': 'application/json'},
      body: '{"action": "$action"}',
    );
    print('Respond: $action, status=${res.statusCode}, body=${res.body}');
    if (res.statusCode == 200) {
      setState(() {
        _futureRequests = fetchOwnerRequests();
      });
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to $action request: ${res.body}')),
      );
    }
  }

  void _callUser(String phone) async {
    final uri = Uri.parse('tel:$phone');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not launch phone app.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Owner Requests'),
        backgroundColor: Colors.green.shade700,
      ),
      body: FutureBuilder<List<dynamic>>(
        future: _futureRequests,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final requests = snapshot.data ?? [];
          if (requests.isEmpty) {
            return const Center(child: Text('No requests found.'));
          }
          return ListView.builder(
            itemCount: requests.length,
            itemBuilder: (context, idx) {
              final req = requests[idx];
              final isPending = req['status'] == 'pending';
              final isAccepted = req['status'] == 'accepted';
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                elevation: 5,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(req['item_name'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                            decoration: BoxDecoration(
                              color: isAccepted ? Colors.green.shade100 : req['status'] == 'declined' ? Colors.red.shade100 : Colors.yellow.shade100,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              req['status'].toString().toUpperCase(),
                              style: TextStyle(
                                color: isAccepted ? Colors.green.shade800 : req['status'] == 'declined' ? Colors.red.shade800 : Colors.orange.shade800,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text('Date: ${req['date']}', style: const TextStyle(fontSize: 16)),
                      Text('Slot: ${req['time_slot']}', style: const TextStyle(fontSize: 16)),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          const Icon(Icons.person, size: 18, color: Colors.grey),
                          const SizedBox(width: 4),
                          Text(req['user_name'] ?? '', style: const TextStyle(fontSize: 15)),
                        ],
                      ),
                      Row(
                        children: [
                          const Icon(Icons.phone, size: 18, color: Colors.grey),
                          const SizedBox(width: 4),
                          Text(req['contact_phone'] ?? '', style: const TextStyle(fontSize: 15)),
                          const SizedBox(width: 8),
                          IconButton(
                            icon: const Icon(Icons.call, color: Color(0xFF2E7D32)),
                            tooltip: 'Call User',
                            onPressed: () => _callUser(req['contact_phone'] ?? ''),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (isPending)
                        Row(
                          children: [
                            Expanded(
                              child: ElevatedButton(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.green.shade700,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                                onPressed: () => _respondToRequest(req['id'], 'accept'),
                                child: const Text('Accept'),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: ElevatedButton(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.red.shade700,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                                onPressed: () => _respondToRequest(req['id'], 'decline'),
                                child: const Text('Decline'),
                              ),
                            ),
                          ],
                        ),
                      if (isAccepted)
                        Padding(
                          padding: const EdgeInsets.only(top: 8.0),
                          child: Text('This slot is now confirmed and blocked for this user.', style: TextStyle(color: Colors.green.shade800, fontWeight: FontWeight.bold)),
                        ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
