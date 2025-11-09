import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'auth_service.dart';

class CropPricesScreen extends StatefulWidget {
  const CropPricesScreen({Key? key}) : super(key: key);

  @override
  State<CropPricesScreen> createState() => _CropPricesScreenState();
}

class _CropPricesScreenState extends State<CropPricesScreen> {
  final _baseUrl = '$baseUrl/api/crop-prices/';  // Added trailing slash
  
  // Controllers and form data
  final _cropController = TextEditingController();
  final _districtController = TextEditingController();
  
  String? _selectedState;
  bool _isLoading = false;
  Map<String, dynamic>? _priceData;
  String? _errorMessage;
  
  // Available states
  final List<String> _states = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
  ];
  
  // Common crops for quick selection
  final List<Map<String, String>> _popularCrops = [
    {"name": "Tomato", "icon": "🍅"},
    {"name": "Onion", "icon": "🧅"},
    {"name": "Potato", "icon": "🥔"},
    {"name": "Rice", "icon": "🌾"},
    {"name": "Wheat", "icon": "🌾"},
    {"name": "Maize", "icon": "🌽"},
    {"name": "Cotton", "icon": "⚪"},
    {"name": "Soybean", "icon": "🫘"},
  ];
  
  @override
  void dispose() {
    _cropController.dispose();
    _districtController.dispose();
    super.dispose();
  }
  
  Future<void> _fetchCropPrice() async {
    if (_cropController.text.trim().isEmpty) {
      _showSnackBar('Please enter a crop name', isError: true);
      return;
    }
    
    if (_selectedState == null) {
      _showSnackBar('Please select a state', isError: true);
      return;
    }
    
    if (_districtController.text.trim().isEmpty) {
      _showSnackBar('Please enter a district name', isError: true);
      return;
    }
    
    setState(() {
      _isLoading = true;
      _priceData = null;
      _errorMessage = null;
    });
    
    try {
      final uri = Uri.parse(_baseUrl).replace(queryParameters: {
        'crop_name': _cropController.text.trim(),
        'state': _selectedState!,
        'district': _districtController.text.trim(),
      });
      
      final response = await http.get(uri);
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _priceData = data;
          _isLoading = false;
        });
      } else {
        final error = jsonDecode(response.body);
        setState(() {
          _errorMessage = error['error'] ?? 'Failed to fetch price data';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Network error: ${e.toString()}';
        _isLoading = false;
      });
    }
  }
  
  void _showSnackBar(String message, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? Colors.red.shade600 : Colors.green.shade600,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
  
  void _selectPopularCrop(String cropName) {
    _cropController.text = cropName;
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        backgroundColor: Colors.orange.shade700,
        elevation: 0,
        title: Row(
          children: [
            Icon(Icons.trending_up, size: 28),
            const SizedBox(width: 8),
            const Text('Real-Time Crop Prices'),
          ],
        ),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header gradient section
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.orange.shade700, Colors.orange.shade500],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 30),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Check Market Prices',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Get latest mandi prices from AGMARKNET',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.white.withOpacity(0.9),
                    ),
                  ),
                ],
              ),
            ),
            
            // Search form
            Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.grey.shade300,
                    blurRadius: 10,
                    offset: Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Popular crops quick select
                  Text(
                    'Popular Crops',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _popularCrops.map((crop) {
                      final isSelected = _cropController.text == crop['name'];
                      return InkWell(
                        onTap: () => _selectPopularCrop(crop['name']!),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: isSelected ? Colors.orange.shade100 : Colors.grey.shade100,
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: isSelected ? Colors.orange.shade700 : Colors.grey.shade300,
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(crop['icon']!, style: TextStyle(fontSize: 18)),
                              const SizedBox(width: 6),
                              Text(
                                crop['name']!,
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                  color: isSelected ? Colors.orange.shade900 : Colors.black87,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                  
                  const SizedBox(height: 24),
                  
                  // Crop name input
                  TextField(
                    controller: _cropController,
                    decoration: InputDecoration(
                      labelText: 'Crop Name',
                      hintText: 'e.g., Tomato, Onion, Rice',
                      prefixIcon: Icon(Icons.agriculture, color: Colors.orange.shade700),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide(color: Colors.orange.shade700, width: 2),
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // State dropdown
                  DropdownButtonFormField<String>(
                    value: _selectedState,
                    decoration: InputDecoration(
                      labelText: 'State',
                      prefixIcon: Icon(Icons.location_on, color: Colors.orange.shade700),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide(color: Colors.orange.shade700, width: 2),
                      ),
                    ),
                    items: _states.map((state) {
                      return DropdownMenuItem(
                        value: state,
                        child: Text(state),
                      );
                    }).toList(),
                    onChanged: (value) {
                      setState(() {
                        _selectedState = value;
                      });
                    },
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // District input
                  TextField(
                    controller: _districtController,
                    decoration: InputDecoration(
                      labelText: 'District',
                      hintText: 'e.g., Nashik, Pune',
                      prefixIcon: Icon(Icons.place, color: Colors.orange.shade700),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide(color: Colors.orange.shade700, width: 2),
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 20),
                  
                  // Search button
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      onPressed: _isLoading ? null : _fetchCropPrice,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.orange.shade700,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: _isLoading
                          ? SizedBox(
                              height: 24,
                              width: 24,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                              ),
                            )
                          : Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.search, size: 24),
                                const SizedBox(width: 8),
                                Text(
                                  'Get Price',
                                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                                ),
                              ],
                            ),
                    ),
                  ),
                ],
              ),
            ),
            
            // Price result card
            if (_priceData != null) _buildPriceCard(),
            
            // Error message
            if (_errorMessage != null) _buildErrorCard(),
            
            // Info section
            _buildInfoSection(),
          ],
        ),
      ),
    );
  }
  
  Widget _buildPriceCard() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.green.shade400, Colors.green.shade600],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.green.shade300,
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.check_circle, color: Colors.white, size: 28),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Price Found!',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
              if (_priceData!['cached'] == true)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    'CACHED',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
            ],
          ),
          
          const SizedBox(height: 20),
          
          // Crop name
          Text(
            _priceData!['crop_name'],
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          
          const SizedBox(height: 8),
          
          // Location
          Row(
            children: [
              Icon(Icons.location_on, color: Colors.white.withOpacity(0.9), size: 18),
              const SizedBox(width: 4),
              Text(
                '${_priceData!['district']}, ${_priceData!['state']}',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.white.withOpacity(0.9),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 4),
          
          // Market
          Row(
            children: [
              Icon(Icons.store, color: Colors.white.withOpacity(0.9), size: 18),
              const SizedBox(width: 4),
              Text(
                _priceData!['market'],
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.white.withOpacity(0.9),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 20),
          
          // Price display
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Price per kg',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey.shade700,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '₹${_priceData!['price_per_kg']}',
                          style: TextStyle(
                            fontSize: 32,
                            fontWeight: FontWeight.bold,
                            color: Colors.green.shade700,
                          ),
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.green.shade50,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        Icons.currency_rupee,
                        size: 32,
                        color: Colors.green.shade700,
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 12),
                Divider(),
                const SizedBox(height: 12),
                
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Modal Price (per quintal)',
                      style: TextStyle(
                        fontSize: 13,
                        color: Colors.grey.shade700,
                      ),
                    ),
                    Text(
                      '₹${_priceData!['modal_price_per_quintal']}',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 12),
          
          // Date
          Row(
            children: [
              Icon(Icons.calendar_today, color: Colors.white.withOpacity(0.9), size: 16),
              const SizedBox(width: 6),
              Text(
                'As of ${_priceData!['date']}',
                style: TextStyle(
                  fontSize: 13,
                  color: Colors.white.withOpacity(0.9),
                  fontStyle: FontStyle.italic,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
  
  Widget _buildErrorCard() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.red.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.red.shade300),
      ),
      child: Row(
        children: [
          Icon(Icons.error_outline, color: Colors.red.shade700, size: 32),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'No Data Found',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.red.shade900,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _errorMessage!,
                  style: TextStyle(
                    fontSize: 13,
                    color: Colors.red.shade700,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildInfoSection() {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.blue.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.blue.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.info_outline, color: Colors.blue.shade700, size: 24),
              const SizedBox(width: 8),
              Text(
                'About This Service',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue.shade900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            '• Prices are sourced from AGMARKNET (Government of India)',
            style: TextStyle(fontSize: 13, color: Colors.blue.shade900, height: 1.5),
          ),
          Text(
            '• Data is updated daily from various mandis across India',
            style: TextStyle(fontSize: 13, color: Colors.blue.shade900, height: 1.5),
          ),
          Text(
            '• If today\'s data is unavailable, the most recent price is shown',
            style: TextStyle(fontSize: 13, color: Colors.blue.shade900, height: 1.5),
          ),
          Text(
            '• Prices may vary between different markets in the same district',
            style: TextStyle(fontSize: 13, color: Colors.blue.shade900, height: 1.5),
          ),
        ],
      ),
    );
  }
}

