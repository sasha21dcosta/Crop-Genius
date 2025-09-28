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
      appBar: AppBar(title: Text("Register")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: SingleChildScrollView(
          child: Column(children: [
            TextField(controller: _nameController, decoration: InputDecoration(labelText: "Name")),
            TextField(controller: _phoneController, decoration: InputDecoration(labelText: "Phone Number"), keyboardType: TextInputType.phone),
            TextField(controller: _cityController, decoration: InputDecoration(labelText: "City")),
            TextField(controller: _addressController, decoration: InputDecoration(labelText: "Address")),
            TextField(controller: _usernameController, decoration: InputDecoration(labelText: "Username")),
            TextField(controller: _emailController, decoration: InputDecoration(labelText: "Email"), keyboardType: TextInputType.emailAddress),
            TextField(controller: _passwordController, decoration: InputDecoration(labelText: "Password"), obscureText: true),
            SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _preferredLanguage,
              decoration: InputDecoration(labelText: 'Preferred Language'),
              items: const [
                DropdownMenuItem(value: 'English', child: Text('English')),
                DropdownMenuItem(value: 'Hindi', child: Text('Hindi')),
                DropdownMenuItem(value: 'Marathi', child: Text('Marathi')),
              ],
              onChanged: (val) => setState(() => _preferredLanguage = val ?? 'English'),
            ),
            SizedBox(height: 20),
            ElevatedButton(onPressed: _register, child: Text("Register")),
          ]),
        ),
      ),
    );
  }
}
