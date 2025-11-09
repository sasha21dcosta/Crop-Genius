import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'auth_service.dart';

class CropRecommendationScreen extends StatefulWidget {
  const CropRecommendationScreen({Key? key}) : super(key: key);

  @override
  State<CropRecommendationScreen> createState() => _CropRecommendationScreenState();
}

class _CropRecommendationScreenState extends State<CropRecommendationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nController = TextEditingController();
  final _pController = TextEditingController();
  final _kController = TextEditingController();
  final _phController = TextEditingController();
  
  bool _loading = false;
  Map<String, dynamic>? _recommendation;
  List<Map<String, dynamic>> _history = [];

  @override
  void initState() {
    super.initState();
    _loadRecommendationHistory();
  }

  @override
  void dispose() {
    _nController.dispose();
    _pController.dispose();
    _kController.dispose();
    _phController.dispose();
    super.dispose();
  }

  Future<void> _loadRecommendationHistory() async {
    try {
      final token = await getToken();
      final response = await http.get(
        Uri.parse('$baseUrl/api/crop/history/'),
        headers: {'Authorization': 'Token $token'},
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _history = List<Map<String, dynamic>>.from(data['recommendations']);
        });
      }
    } catch (e) {
      print('Error loading history: $e');
    }
  }

  Future<void> _getRecommendation() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _loading = true);

    try {
      final token = await getToken();
      final response = await http.post(
        Uri.parse('$baseUrl/api/crop/recommend/'),
        headers: {
          'Authorization': 'Token $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'n_content': double.parse(_nController.text),
          'p_content': double.parse(_pController.text),
          'k_content': double.parse(_kController.text),
          'ph': double.parse(_phController.text),
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _recommendation = data['recommendation'];
        });
        _loadRecommendationHistory(); // Refresh history
      } else {
        _showErrorDialog('Failed to get recommendation: ${response.body}');
      }
    } catch (e) {
      _showErrorDialog('Error: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Error'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.green.shade50,
      appBar: AppBar(
        title: const Text('Crop Recommendation 🌱'),
        backgroundColor: Colors.green.shade700,
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.green.shade400, Colors.green.shade600],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(15),
              ),
              child: Column(
                children: [
                  Icon(Icons.eco, size: 50, color: Colors.white),
                  const SizedBox(height: 10),
                  const Text(
                    'AI-Powered Crop Recommendation',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 5),
                  const Text(
                    'Get personalized crop suggestions based on your soil conditions',
                    style: TextStyle(color: Colors.white70),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 20),
            
            // Input Form
            Card(
              elevation: 4,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Soil Analysis Input',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 15),
                      
                      // N Content
                      TextFormField(
                        controller: _nController,
                        decoration: const InputDecoration(
                          labelText: 'Nitrogen Content (N)',
                          hintText: 'Enter N content (0-200)',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.science),
                        ),
                        keyboardType: TextInputType.number,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter N content';
                          }
                          final n = double.tryParse(value);
                          if (n == null || n < 0 || n > 200) {
                            return 'N content must be between 0 and 200';
                          }
                          return null;
                        },
                      ),
                      
                      const SizedBox(height: 15),
                      
                      // P Content
                      TextFormField(
                        controller: _pController,
                        decoration: const InputDecoration(
                          labelText: 'Phosphorus Content (P)',
                          hintText: 'Enter P content (0-200)',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.science),
                        ),
                        keyboardType: TextInputType.number,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter P content';
                          }
                          final p = double.tryParse(value);
                          if (p == null || p < 0 || p > 200) {
                            return 'P content must be between 0 and 200';
                          }
                          return null;
                        },
                      ),
                      
                      const SizedBox(height: 15),
                      
                      // K Content
                      TextFormField(
                        controller: _kController,
                        decoration: const InputDecoration(
                          labelText: 'Potassium Content (K)',
                          hintText: 'Enter K content (0-200)',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.science),
                        ),
                        keyboardType: TextInputType.number,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter K content';
                          }
                          final k = double.tryParse(value);
                          if (k == null || k < 0 || k > 200) {
                            return 'K content must be between 0 and 200';
                          }
                          return null;
                        },
                      ),
                      
                      const SizedBox(height: 15),
                      
                      // pH Level
                      TextFormField(
                        controller: _phController,
                        decoration: const InputDecoration(
                          labelText: 'Soil pH Level',
                          hintText: 'Enter pH (0-14)',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.analytics),
                        ),
                        keyboardType: TextInputType.number,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter pH level';
                          }
                          final ph = double.tryParse(value);
                          if (ph == null || ph < 0 || ph > 14) {
                            return 'pH must be between 0 and 14';
                          }
                          return null;
                        },
                      ),
                      
                      const SizedBox(height: 20),
                      
                      // Submit Button
                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: ElevatedButton.icon(
                          onPressed: _loading ? null : _getRecommendation,
                          icon: _loading 
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Icon(Icons.psychology),
                          label: Text(_loading ? 'Analyzing...' : 'Get Recommendation'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green.shade700,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            
            const SizedBox(height: 20),
            
            // Recommendation Result
            if (_recommendation != null) ...[
              Card(
                elevation: 4,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.emoji_events, color: Colors.amber.shade600, size: 30),
                          const SizedBox(width: 10),
                          const Text(
                            'Recommendation Result',
                            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                      const SizedBox(height: 15),
                      
                      // Main Recommendation
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(15),
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: Colors.green.shade200),
                        ),
                        child: Column(
                          children: [
                            Text(
                              _recommendation!['predicted_crop'],
                              style: const TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                                color: Colors.green,
                              ),
                            ),
                            const SizedBox(height: 5),
                            Text(
                              'Confidence: ${(_recommendation!['confidence_score'] * 100).toStringAsFixed(1)}%',
                              style: TextStyle(
                                fontSize: 16,
                                color: Colors.green.shade700,
                              ),
                            ),
                          ],
                        ),
                      ),
                      
                      const SizedBox(height: 15),
                      
                      // Alternative Crops
                      if (_recommendation!['alternative_crops'].isNotEmpty) ...[
                        const Text(
                          'Alternative Options:',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 10),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: (_recommendation!['alternative_crops'] as List)
                              .map((crop) => Chip(
                                    label: Text(crop),
                                    backgroundColor: Colors.blue.shade50,
                                    side: BorderSide(color: Colors.blue.shade200),
                                  ))
                              .toList(),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
            
            const SizedBox(height: 20),
            
            // History Section
            if (_history.isNotEmpty) ...[
              const Text(
                'Recent Recommendations',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),
              ...(_history.take(3).map((item) => Card(
                margin: const EdgeInsets.only(bottom: 10),
                child: ListTile(
                  leading: Icon(Icons.agriculture, color: Colors.green.shade600),
                  title: Text(item['predicted_crop']),
                  subtitle: Text('Confidence: ${(item['confidence_score'] * 100).toStringAsFixed(1)}%'),
                  trailing: Text(
                    DateTime.parse(item['created_at']).toString().split(' ')[0],
                    style: const TextStyle(fontSize: 12),
                  ),
                ),
              ))),
            ],
          ],
        ),
      ),
    );
  }
}
