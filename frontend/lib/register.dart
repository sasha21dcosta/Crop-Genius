import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'auth_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'home.dart';

class RegisterPage extends StatefulWidget {
  const RegisterPage({Key? key}) : super(key: key);

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _cityController = TextEditingController();
  final _addressController = TextEditingController();
  final _usernameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  String _preferredLanguage = 'English';
  List<String> _selectedCrops = [];
  final List<Map<String, String>> _cropOptions = [
    {'key': 'rice', 'label': 'Rice'},
    {'key': 'wheat', 'label': 'Wheat'},
    {'key': 'apple', 'label': 'Apple'},
    {'key': 'tomato', 'label': 'Tomato'},
    {'key': 'potato', 'label': 'Potato'},
  ];

  void _register() async {
    var response = await http.post(
      Uri.parse("$baseUrl/api/register/"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        'name': _nameController.text,
        'phone': _phoneController.text,
        'city': _cityController.text,
        'address': _addressController.text,
        'username': _usernameController.text,
        'email': _emailController.text,
        'password': _passwordController.text,
        'preferred_language': _preferredLanguage,
        'crops': _selectedCrops,
      }),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final data = jsonDecode(response.body);
      print("REGISTER SUCCESS: Token:  ${data['token']}");
      // Save token to SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('token', data['token']);
      final userName = data['name'] ?? data['username'] ?? 'User';
      // Navigate to home page directly
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => HomePage(userName: userName)),
      );
    } else {
      print("REGISTER FAILED:  ${response.body}");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Registration failed. Please check your details.")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        title: const Text("Create Account"),
        backgroundColor: Colors.green.shade700,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Header Section
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(30),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.green.shade700, Colors.green.shade500],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
              child: Column(
                children: [
                  Icon(Icons.agriculture, size: 60, color: Colors.white),
                  const SizedBox(height: 12),
                  const Text(
                    'Join CropGenius',
                    style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Start your smart farming journey today',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.white.withOpacity(0.9),
                    ),
                  ),
                ],
              ),
            ),
            
            // Form Section
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Personal Information',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  _buildTextField(_nameController, "Full Name", Icons.person, TextInputType.text),
                  const SizedBox(height: 12),
                  _buildTextField(_phoneController, "Phone Number", Icons.phone, TextInputType.phone),
                  const SizedBox(height: 12),
                  _buildTextField(_cityController, "City", Icons.location_city, TextInputType.text),
                  const SizedBox(height: 12),
                  _buildTextField(_addressController, "Address", Icons.home, TextInputType.text),
                  
                  const SizedBox(height: 24),
                  const Text(
                    'Account Details',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  _buildTextField(_usernameController, "Username", Icons.account_circle, TextInputType.text),
                  const SizedBox(height: 12),
                  _buildTextField(_emailController, "Email", Icons.email, TextInputType.emailAddress),
                  const SizedBox(height: 12),
                  _buildTextField(_passwordController, "Password", Icons.lock, TextInputType.text, obscureText: true),
                  const SizedBox(height: 20),
                  // Farming Information
                  const Text(
                    'Farming Information',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  // Crops Selection
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.green.shade200),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.eco, color: Colors.green.shade700, size: 22),
                            const SizedBox(width: 8),
                            const Text(
                              'Crops Grown (Select all that apply)',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                                color: Colors.black87,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: _cropOptions.map((crop) {
                            final selected = _selectedCrops.contains(crop['key']);
                            return FilterChip(
                              label: Text(crop['label']!),
                              selected: selected,
                              onSelected: (val) {
                                setState(() {
                                  if (val) {
                                    _selectedCrops.add(crop['key']!);
                                  } else {
                                    _selectedCrops.remove(crop['key']!);
                                  }
                                });
                              },
                              selectedColor: Colors.green.shade200,
                              checkmarkColor: Colors.green.shade800,
                              backgroundColor: Colors.grey.shade200,
                              labelStyle: TextStyle(
                                color: selected ? Colors.green.shade800 : Colors.black87,
                                fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                              ),
                            );
                          }).toList(),
                        ),
                        if (_selectedCrops.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: Colors.green.shade50,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              '✓ Selected: ${_selectedCrops.map((c) => _cropOptions.firstWhere((opt) => opt['key'] == c)['label']).join(', ')}',
                              style: TextStyle(
                                color: Colors.green.shade800,
                                fontWeight: FontWeight.w500,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // Language Dropdown
                  DropdownButtonFormField<String>(
                    value: _preferredLanguage,
                    decoration: InputDecoration(
                      labelText: 'Preferred Language',
                      prefixIcon: Icon(Icons.language, color: Colors.green.shade700),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                    items: const [
                      DropdownMenuItem(value: 'English', child: Text('English')),
                      DropdownMenuItem(value: 'Hindi', child: Text('Hindi (हिंदी)')),
                      DropdownMenuItem(value: 'Marathi', child: Text('Marathi (मराठी)')),
                    ],
                    onChanged: (val) => setState(() => _preferredLanguage = val ?? 'English'),
                  ),
                  
                  const SizedBox(height: 30),
                  
                  // Register Button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _register,
                      icon: const Icon(Icons.check_circle, size: 24),
                      label: const Text(
                        "Create Account",
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green.shade700,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTextField(
    TextEditingController controller,
    String label,
    IconData icon,
    TextInputType keyboardType, {
    bool obscureText = false,
  }) {
    return TextField(
      controller: controller,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: Colors.green.shade700),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        filled: true,
        fillColor: Colors.white,
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey.shade300),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.green.shade700, width: 2),
        ),
      ),
      keyboardType: keyboardType,
      obscureText: obscureText,
    );
  }
}
