import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'marketplace.dart';
import 'auth_service.dart';
import 'diagnosis_chat.dart';
import 'crop_recommendation.dart';
import 'profile.dart';
import 'crop_prices.dart';
import 'package:url_launcher/url_launcher.dart';

class HomePage extends StatefulWidget {
  final String userName;
  const HomePage({Key? key, required this.userName}) : super(key: key);

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  List<dynamic> weatherAlerts = [];
  bool isLoadingAlerts = true;

  @override
  void initState() {
    super.initState();
    _fetchWeatherAlerts();
  }

  Future<void> _fetchWeatherAlerts() async {
    try {
      final token = await getToken();
      print('🔍 Fetching weather alerts...');
      print('🔑 Token: ${token?.substring(0, 10)}...');
      print('🌐 URL: $baseUrl/api/weather/alerts/active/');
      
      final response = await http.get(
        Uri.parse('$baseUrl/api/weather/alerts/active/'),
        headers: {'Authorization': 'Token $token'},
      );
      
      print('📡 Response status: ${response.statusCode}');
      print('📦 Response body: ${response.body}');
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('✅ Alerts count: ${data['alerts']?.length ?? 0}');
        setState(() {
          weatherAlerts = data['alerts'] ?? [];
          isLoadingAlerts = false;
        });
      } else {
        print('❌ Error: ${response.statusCode}');
        setState(() {
          isLoadingAlerts = false;
        });
      }
    } catch (e) {
      print('❌ Error fetching weather alerts: $e');
      setState(() {
        isLoadingAlerts = false;
      });
    }
  }

  Future<void> _markAlertAsRead(int alertId) async {
    try {
      final token = await getToken();
      await http.post(
        Uri.parse('$baseUrl/api/weather/alerts/$alertId/read/'),
        headers: {'Authorization': 'Token $token'},
      );
      // Refresh alerts after marking as read
      _fetchWeatherAlerts();
    } catch (e) {
      print('Error marking alert as read: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      body: CustomScrollView(
        slivers: [
          // Modern App Bar with gradient
          SliverAppBar(
            expandedHeight: 280,
            floating: false,
            pinned: true,
            backgroundColor: Colors.green.shade700,
            flexibleSpace: FlexibleSpaceBar(
              background: Stack(
                fit: StackFit.expand,
                children: [
                  // Background Image
                  Image.network(
                    'https://plus.unsplash.com/premium_photo-1661962692059-55d5a4319814?w=600&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8YWdyaWN1bHR1cmV8ZW58MHx8MHx8fDA%3D',
                    fit: BoxFit.cover,
                  ),
                  // Gradient Overlay
                  Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.black.withOpacity(0.3),
                          Colors.green.shade900.withOpacity(0.8),
                        ],
                      ),
                    ),
                  ),
                  // Welcome Content
                  Positioned(
                    bottom: 20,
                    left: 20,
                    right: 20,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          '🌾 CropGenius',
                          style: TextStyle(
                            fontSize: 32,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                            shadows: [
                              Shadow(
                                blurRadius: 10.0,
                                color: Colors.black45,
                                offset: Offset(2, 2),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Welcome back, ${widget.userName}!',
                          style: const TextStyle(
                            fontSize: 18,
                            color: Colors.white,
                            fontWeight: FontWeight.w500,
                            shadows: [
                              Shadow(
                                blurRadius: 8.0,
                                color: Colors.black45,
                                offset: Offset(1, 1),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          'Empowering farmers with smart agriculture',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.white70,
                            shadows: [
                              Shadow(
                                blurRadius: 8.0,
                                color: Colors.black45,
                                offset: Offset(1, 1),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            actions: [
              IconButton(
                icon: Stack(
                  children: [
                    const Icon(Icons.notifications_outlined, size: 28),
                    Positioned(
                      right: 0,
                      top: 0,
                      child: Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: Colors.red,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        constraints: const BoxConstraints(
                          minWidth: 8,
                          minHeight: 8,
                        ),
                      ),
                    ),
                  ],
                ),
                tooltip: 'Owner Requests',
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const OwnerRequestsPage()),
                  );
                },
              ),
              IconButton(
                icon: const Icon(Icons.account_circle, size: 28),
                tooltip: 'My Profile',
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const ProfilePage()),
                  );
                },
              ),
              const SizedBox(width: 8),
            ],
          ),
          
          // Content
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Quick Stats Section
                  const SizedBox(height: 10),
              
                  // Weather Alerts Section (if any)
                  if (!isLoadingAlerts && weatherAlerts.isNotEmpty) ...[
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.warning_amber_rounded, color: Colors.red.shade700, size: 24),
                            const SizedBox(width: 8),
                            const Text(
                              'Weather Alerts',
                              style: TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.bold,
                                color: Colors.black87,
                              ),
                            ),
                          ],
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: Colors.red.shade100,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            '${weatherAlerts.length}',
                            style: TextStyle(
                              color: Colors.red.shade900,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Disease risk warnings based on current weather',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                      ),
                    ),
                    const SizedBox(height: 16),
                    
                    // Weather Alert Cards
                    ...weatherAlerts.map((alert) => _buildWeatherAlertCard(alert)).toList(),
                    
                    const SizedBox(height: 30),
                  ],
                  
                  // Features Section
                  const Text(
                    'Our Services',
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'AI-powered solutions for modern farming',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(height: 20),
                  
                  _modernFeatureCard(
                    context,
                    icon: Icons.psychology,
                    title: 'AI Disease Diagnosis',
                    subtitle: 'Detect crop diseases using AI and get instant treatment recommendations',
                    gradient: LinearGradient(
                      colors: [Colors.green.shade400, Colors.green.shade700],
                    ),
                    route: 'diagnosis',
                  ),
                  
                  _modernFeatureCard(
                    context,
                    icon: Icons.eco,
                    title: 'Smart Crop Recommendation',
                    subtitle: 'Get personalized crop suggestions based on soil and weather conditions',
                    gradient: LinearGradient(
                      colors: [Colors.teal.shade400, Colors.teal.shade700],
                    ),
                    route: 'crop',
                  ),
                  
                  _modernFeatureCard(
                    context,
                    icon: Icons.store,
                    title: 'Marketplace & Equipment Rental',
                    subtitle: 'Buy, sell agricultural products and rent farming equipment',
                    gradient: LinearGradient(
                      colors: [Colors.blue.shade400, Colors.blue.shade700],
                    ),
                    route: 'marketplace',
                  ),
                  
                  _modernFeatureCard(
                    context,
                    icon: Icons.trending_up,
                    title: 'Real-Time Crop Prices',
                    subtitle: 'Stay updated with latest market prices and trends',
                    gradient: LinearGradient(
                      colors: [Colors.orange.shade400, Colors.orange.shade700],
                    ),
                    route: 'prices',
                  ),
                  
                  const SizedBox(height: 20),
                  
                  // Info Banner
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [Colors.amber.shade50, Colors.amber.shade100],
                      ),
                      borderRadius: BorderRadius.circular(15),
                      border: Border.all(color: Colors.amber.shade300),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.wb_sunny, color: Colors.amber.shade700, size: 40),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Farming Tip of the Day',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.amber.shade900,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'Regular soil testing helps optimize fertilizer use and improve crop yield.',
                                style: TextStyle(
                                  fontSize: 13,
                                  color: Colors.amber.shade800,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 30),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _modernFeatureCard(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String subtitle,
    required LinearGradient gradient,
    required String route,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {
            if (route == 'diagnosis') {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const DiagnosisChatScreen()),
              );
            } else if (route == 'crop') {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const CropRecommendationScreen()),
              );
            } else if (route == 'marketplace') {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MarketplaceScreen()),
              );
            } else if (route == 'prices') {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const CropPricesScreen()),
              );
            }
          },
          borderRadius: BorderRadius.circular(16),
          child: Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.shade300,
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: gradient,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(icon, color: Colors.white, size: 32),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        subtitle,
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.grey.shade600,
                          height: 1.3,
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(Icons.arrow_forward_ios, color: Colors.grey.shade400, size: 18),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildWeatherAlertCard(dynamic alert) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.red.shade50, Colors.orange.shade50],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.red.shade200, width: 2),
        boxShadow: [
          BoxShadow(
            color: Colors.red.shade100,
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header with disease name and crop
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.red.shade400, Colors.red.shade600],
              ),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(14),
                topRight: Radius.circular(14),
              ),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(
                    Icons.coronavirus_outlined,
                    color: Colors.white,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        alert['disease_name'] ?? 'Unknown Disease',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: Colors.white,
                        ),
                      ),
                      Text(
                        '${alert['crop_name'] ?? 'Unknown Crop'} - High Risk',
                        style: const TextStyle(
                          fontSize: 13,
                          color: Colors.white,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, color: Colors.white),
                  onPressed: () {
                    _markAlertAsRead(alert['id']);
                  },
                  tooltip: 'Dismiss',
                ),
              ],
            ),
          ),
          
          // Alert message
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.info_outline, color: Colors.orange.shade800, size: 20),
                    const SizedBox(width: 8),
                    const Text(
                      'Weather Alert',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  alert['alert_message'] ?? 'Risk conditions detected',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey.shade800,
                    height: 1.4,
                  ),
                ),
                
                
                // Action button
               
              ],
            ),
          ),
        ],
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
      backgroundColor: Colors.grey.shade100,
      body: CustomScrollView(
        slivers: [
          // Modern SliverAppBar
          SliverAppBar(
            expandedHeight: 200,
            floating: false,
            pinned: true,
            backgroundColor: Colors.green.shade700,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Colors.green.shade700,
                      Colors.green.shade500,
                    ],
                  ),
                ),
                child: Stack(
                  children: [
                    Positioned(
                      bottom: 20,
                      left: 20,
                      right: 20,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: Colors.white.withOpacity(0.2),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: const Icon(
                                  Icons.notifications_active,
                                  color: Colors.white,
                                  size: 32,
                                ),
                              ),
                              const SizedBox(width: 16),
                              const Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Booking Requests',
                                      style: TextStyle(
                                        fontSize: 28,
                                        fontWeight: FontWeight.bold,
                                        color: Colors.white,
                                      ),
                                    ),
                                    SizedBox(height: 4),
                                    Text(
                                      'Manage your rental bookings',
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: Colors.white70,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          
          // Content
          SliverToBoxAdapter(
            child: FutureBuilder<List<dynamic>>(
              future: _futureRequests,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return Container(
                    height: 400,
                    child: const Center(
                      child: CircularProgressIndicator(
                        color: Color(0xFF2E7D32),
                      ),
                    ),
                  );
                }
                
                final requests = snapshot.data ?? [];
                
                if (requests.isEmpty) {
                  return Container(
                    height: 400,
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(30),
                            decoration: BoxDecoration(
                              color: Colors.grey.shade200,
                              shape: BoxShape.circle,
                            ),
                            child: Icon(
                              Icons.event_busy,
                              size: 80,
                              color: Colors.grey.shade400,
                            ),
                          ),
                          const SizedBox(height: 24),
                          Text(
                            'No Booking Requests',
                            style: TextStyle(
                              fontSize: 20,
                              color: Colors.grey.shade700,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Requests will appear here when\nusers book your equipment',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey.shade500,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }
                
                return Padding(
                  padding: const EdgeInsets.fromLTRB(20, 20, 20, 30),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Summary Stats - More subtle
                      Row(
                        children: [
                          Expanded(
                            child: _buildCleanStatCard(
                              'Total',
                              requests.length.toString(),
                              Colors.blue.shade600,
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: _buildCleanStatCard(
                              'Pending',
                              requests.where((r) => r['status'] == 'pending').length.toString(),
                              Colors.amber.shade600,
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: _buildCleanStatCard(
                              'Done',
                              requests.where((r) => r['status'] == 'accepted').length.toString(),
                              Colors.green.shade600,
                            ),
                          ),
                        ],
                      ),
                      
                      const SizedBox(height: 32),
                      
                      // Requests List - no header, let cards speak
                      ...requests.map((req) => _buildCleanRequestCard(req)).toList(),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCleanStatCard(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 13,
              color: color.withOpacity(0.8),
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCleanRequestCard(Map<String, dynamic> req) {
    final isPending = req['status'] == 'pending';
    final isAccepted = req['status'] == 'accepted';
    final isDeclined = req['status'] == 'declined';
    
    Color statusColor = isPending
        ? Colors.amber.shade700
        : isAccepted
            ? Colors.green.shade600
            : Colors.grey.shade600;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 15,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Equipment Name & Status
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      req['item_name'] ?? 'Unknown Item',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 20,
                        color: Colors.black87,
                        height: 1.2,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: statusColor,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          req['status'].toString().toLowerCase().replaceFirst(
                            req['status'].toString()[0],
                            req['status'].toString()[0].toUpperCase()
                          ),
                          style: TextStyle(
                            fontSize: 14,
                            color: statusColor,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 20),
          
          // Date & Time - Cleaner layout
          Row(
            children: [
              Icon(Icons.calendar_today, size: 18, color: Colors.grey.shade600),
              const SizedBox(width: 8),
              Text(
                req['date'] ?? '',
                style: const TextStyle(
                  fontSize: 15,
                  color: Colors.black87,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 20),
              Icon(Icons.access_time, size: 18, color: Colors.grey.shade600),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  req['time_slot'] ?? '',
                  style: const TextStyle(
                    fontSize: 15,
                    color: Colors.black87,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 20),
          
          // Divider
          Container(
            height: 1,
            color: Colors.grey.shade200,
          ),
          
          const SizedBox(height: 20),
          
          // Customer Info - Simplified
          Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: Colors.green.shade100,
                child: Icon(
                  Icons.person,
                  color: Colors.green.shade700,
                  size: 26,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      req['user_name'] ?? 'Anonymous',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      req['contact_phone'] ?? 'No phone',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                decoration: BoxDecoration(
                  color: Colors.green.shade600,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: IconButton(
                  icon: const Icon(Icons.phone, color: Colors.white, size: 20),
                  tooltip: 'Call',
                  onPressed: () => _callUser(req['contact_phone'] ?? ''),
                ),
              ),
            ],
          ),
          
          // Action Buttons - Cleaner
          if (isPending) ...[
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green.shade600,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                    onPressed: () => _respondToRequest(req['id'], 'accept'),
                    child: const Text(
                      'Accept',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.grey.shade200,
                      foregroundColor: Colors.red.shade700,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                    onPressed: () => _respondToRequest(req['id'], 'decline'),
                    child: const Text(
                      'Decline',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
          
          if (isAccepted) ...[
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Icon(Icons.check_circle, color: Colors.green.shade700, size: 22),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Booking confirmed & reserved',
                      style: TextStyle(
                        color: Colors.green.shade900,
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
          
          if (isDeclined) ...[
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Icon(Icons.block, color: Colors.grey.shade600, size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Request declined',
                      style: TextStyle(
                        color: Colors.grey.shade700,
                        fontWeight: FontWeight.w500,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

