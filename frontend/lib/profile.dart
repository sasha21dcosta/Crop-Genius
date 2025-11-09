import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'package:image_picker/image_picker.dart';
import 'auth_service.dart';
import 'edit_profile.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({Key? key}) : super(key: key);

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  Map<String, dynamic>? _profileData;
  bool _loading = true;
  File? _profileImage;
  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final token = await getToken();
      if (token == null) {
        setState(() => _loading = false);
        return;
      }

      final response = await http.get(
        Uri.parse('$baseUrl/api/user/profile/'),
        headers: {'Authorization': 'Token $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // Build full URL from relative path (if not already absolute)
        if (data['profile_photo_url'] != null && !data['profile_photo_url'].toString().startsWith('http')) {
          data['profile_photo_url'] = '$baseUrl${data['profile_photo_url']}';
        }
        
        print('📸 Profile photo URL (backend): ${data['profile_photo_url']}');
        setState(() {
          _profileData = data;
          _loading = false;
        });
      } else {
        print('Error loading profile: ${response.statusCode}');
        setState(() => _loading = false);
      }
    } catch (e) {
      print('Error loading profile: $e');
      setState(() => _loading = false);
    }
  }

  Future<void> _pickImage() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 512,
        maxHeight: 512,
        imageQuality: 85,
      );

      if (image != null) {
        setState(() {
          _profileImage = File(image.path);
        });
        
        // Upload to backend immediately
        await _uploadProfilePhoto(File(image.path));
      }
    } catch (e) {
      print('Error picking image: $e');
    }
  }

  Future<void> _uploadProfilePhoto(File imageFile) async {
    try {
      final token = await getToken();
      if (token == null) return;

      var request = http.MultipartRequest(
        'PATCH',
        Uri.parse('$baseUrl/api/user/profile/'),
      );

      request.headers['Authorization'] = 'Token $token';
      request.files.add(
        await http.MultipartFile.fromPath('profile_photo', imageFile.path),
      );

      final response = await request.send();

      if (response.statusCode == 200) {
        // Clear local image and reload from server
        setState(() {
          _profileImage = null;  // Clear local image
        });
        
        await _loadProfile(); // Reload profile to get new photo URL
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('✅ Profile photo updated!'),
              backgroundColor: Colors.green,
            ),
          );
        }
      } else {
        final responseBody = await response.stream.bytesToString();
        print('Upload failed: $responseBody');
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to upload photo')),
          );
        }
      }
    } catch (e) {
      print('Error uploading photo: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text('My Profile'),
        backgroundColor: Colors.green.shade700,
        elevation: 0,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _profileData == null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline, size: 60, color: Colors.grey.shade400),
                      const SizedBox(height: 16),
                      Text(
                        'Failed to load profile',
                        style: TextStyle(color: Colors.grey.shade600, fontSize: 18),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        onPressed: _loadProfile,
                        icon: const Icon(Icons.refresh),
                        label: const Text('Retry'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green.shade700,
                        ),
                      ),
                    ],
                  ),
                )
              : SingleChildScrollView(
                  child: Column(
                    children: [
                      // Header with gradient background
                      Container(
                        width: double.infinity,
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [Colors.green.shade700, Colors.green.shade500],
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                          ),
                        ),
                        padding: const EdgeInsets.only(bottom: 80, top: 20),
                        child: Column(
                          children: [
                            // Profile Photo
                            Stack(
                              children: [
                                CircleAvatar(
                                  radius: 70,
                                  backgroundColor: Colors.white,
                                  child: CircleAvatar(
                                    radius: 65,
                                    backgroundColor: Colors.green.shade100,
                                    backgroundImage: _profileImage != null
                                        ? FileImage(_profileImage!)
                                        : (_profileData!['profile_photo_url'] != null
                                            ? NetworkImage(_profileData!['profile_photo_url'])
                                            : null) as ImageProvider?,
                                    child: (_profileImage == null && _profileData!['profile_photo_url'] == null)
                                        ? Icon(
                                            Icons.person,
                                            size: 70,
                                            color: Colors.green.shade700,
                                          )
                                        : null,
                                  ),
                                ),
                                Positioned(
                                  bottom: 0,
                                  right: 0,
                                  child: GestureDetector(
                                    onTap: _pickImage,
                                    child: Container(
                                      padding: const EdgeInsets.all(8),
                                      decoration: BoxDecoration(
                                        color: Colors.green.shade600,
                                        shape: BoxShape.circle,
                                        border: Border.all(color: Colors.white, width: 3),
                                      ),
                                      child: const Icon(
                                        Icons.camera_alt,
                                        color: Colors.white,
                                        size: 20,
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            Text(
                              _profileData!['name'] ?? 'User',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 26,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '👨‍🌾 Farmer',
                              style: TextStyle(
                                color: Colors.white.withOpacity(0.9),
                                fontSize: 16,
                              ),
                            ),
                          ],
                        ),
                      ),

                      // Profile Details Card
                      Transform.translate(
                        offset: const Offset(0, -60),
                        child: Container(
                          margin: const EdgeInsets.symmetric(horizontal: 20),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(20),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.1),
                                blurRadius: 20,
                                offset: const Offset(0, 10),
                              ),
                            ],
                          ),
                          child: Column(
                            children: [
                              // Personal Information Section
                              _buildSectionHeader('Personal Information', Icons.person_outline),
                              _buildInfoTile(
                                Icons.badge,
                                'Full Name',
                                _profileData!['name'] ?? 'Not set',
                              ),
                              _buildDivider(),
                              _buildInfoTile(
                                Icons.phone,
                                'Phone Number',
                                _profileData!['phone'] ?? 'Not set',
                                trailing: IconButton(
                                  icon: Icon(Icons.call, color: Colors.green.shade700),
                                  onPressed: () {
                                    // Call functionality
                                  },
                                ),
                              ),
                              _buildDivider(),
                              _buildInfoTile(
                                Icons.location_city,
                                'City',
                                _profileData!['city'] ?? 'Not set',
                              ),
                              _buildDivider(),
                              _buildInfoTile(
                                Icons.home,
                                'Address',
                                _profileData!['address'] ?? 'Not set',
                              ),

                              const SizedBox(height: 20),

                              // Farming Information Section
                              _buildSectionHeader('Farming Information', Icons.agriculture),
                              _buildInfoTile(
                                Icons.language,
                                'Preferred Language',
                                _profileData!['preferred_language'] ?? 'English',
                              ),
                              _buildDivider(),
                              
                              // Crops Section
                              Padding(
                                padding: const EdgeInsets.all(16.0),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        Icon(Icons.eco, color: Colors.green.shade700, size: 22),
                                        const SizedBox(width: 12),
                                        const Text(
                                          'My Crops',
                                          style: TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w600,
                                            color: Colors.black87,
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 12),
                                    Wrap(
                                      spacing: 8,
                                      runSpacing: 8,
                                      children: (_profileData!['crops_list'] as List<dynamic>?)
                                              ?.map((crop) => _buildCropChip(crop.toString()))
                                              .toList() ??
                                          [
                                            Text(
                                              'No crops selected',
                                              style: TextStyle(color: Colors.grey.shade600),
                                            )
                                          ],
                                    ),
                                  ],
                                ),
                              ),
                              
                              const SizedBox(height: 20),
                            ],
                          ),
                        ),
                      ),

                      // Edit Profile Button
                      Transform.translate(
                        offset: const Offset(0, -40),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 40),
                          child: SizedBox(
                            width: double.infinity,
                            child: ElevatedButton.icon(
                              onPressed: () async {
                                final result = await Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => EditProfilePage(profileData: _profileData!),
                                  ),
                                );
                                
                                // Reload profile if edited successfully
                                if (result == true) {
                                  _loadProfile();
                                }
                              },
                              icon: const Icon(Icons.edit),
                              label: const Text('Edit Profile'),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.green.shade700,
                                padding: const EdgeInsets.symmetric(vertical: 16),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                textStyle: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }

  Widget _buildSectionHeader(String title, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.green.shade50,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(20),
          topRight: Radius.circular(20),
        ),
      ),
      child: Row(
        children: [
          Icon(icon, color: Colors.green.shade700, size: 24),
          const SizedBox(width: 12),
          Text(
            title,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.green.shade800,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoTile(IconData icon, String label, String value, {Widget? trailing}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          Icon(icon, color: Colors.green.shade700, size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 13,
                    color: Colors.grey.shade600,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 16,
                    color: Colors.black87,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          if (trailing != null) trailing,
        ],
      ),
    );
  }

  Widget _buildDivider() {
    return Divider(
      height: 1,
      thickness: 1,
      color: Colors.grey.shade200,
      indent: 50,
    );
  }

  Widget _buildCropChip(String crop) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.green.shade400, Colors.green.shade600],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.green.shade200,
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.eco, color: Colors.white, size: 16),
          const SizedBox(width: 6),
          Text(
            crop.toUpperCase(),
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }
}

