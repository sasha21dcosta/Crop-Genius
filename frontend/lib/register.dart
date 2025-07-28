import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class RegisterPage extends StatefulWidget {
  const RegisterPage({Key? key}) : super(key: key);

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final _usernameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  void _register() async {
    var response = await http.post(
      Uri.parse("http://10.0.2.2:8000/api/register/"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        'username': _usernameController.text,
        'email': _emailController.text,
        'password': _passwordController.text,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      print("REGISTER SUCCESS: Token: ${data['token']}");
      // Navigate to login screen
      Navigator.pop(context);
    } else {
      print("REGISTER FAILED: ${response.body}");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Register")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          TextField(controller: _usernameController, decoration: InputDecoration(labelText: "Username")),
          TextField(controller: _emailController, decoration: InputDecoration(labelText: "Email")),
          TextField(controller: _passwordController, decoration: InputDecoration(labelText: "Password"), obscureText: true),
          SizedBox(height: 20),
          ElevatedButton(onPressed: _register, child: Text("Register")),
        ]),
      ),
    );
  }
}
