import 'package:flutter/material.dart';

class HomePage extends StatelessWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.green.shade50,
      appBar: AppBar(
        backgroundColor: Colors.green.shade700,
        title: const Text('AgroConnect 🌾'),
        centerTitle: true,
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
              'Welcome Farmer!',
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
            _featureCard(Icons.eco, 'Symptom Input AI diagnosis'),
            _featureCard(Icons.cloud, ' Crop Suggestions'),
            _featureCard(Icons.shopping_cart, 'Equipment Rental'),
            _featureCard(Icons.support, 'real-time crop prices'),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _featureCard(IconData icon, String title) {
    return Card(
      elevation: 4,
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: ListTile(
        leading: Icon(icon, color: Colors.green.shade700, size: 30),
        title: Text(title, style: TextStyle(fontSize: 18)),
        trailing: const Icon(Icons.arrow_forward_ios),
        onTap: () {
          // Add navigation or action
        },
      ),
    );
  }
}
