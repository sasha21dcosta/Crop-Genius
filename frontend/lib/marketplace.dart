import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'auth_service.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

class MarketplaceScreen extends StatefulWidget {
  const MarketplaceScreen({Key? key}) : super(key: key);

  @override
  State<MarketplaceScreen> createState() => _MarketplaceScreenState();
}

class _MarketplaceScreenState extends State<MarketplaceScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _baseUrl = '$baseUrl/api';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  Future<List<dynamic>> _fetchItems(String type) async {
    final res = await http.get(Uri.parse('$_baseUrl/items/?type=$type'));
    if (res.statusCode == 200) {
      return jsonDecode(res.body) as List<dynamic>;
    }
    return [];
  }

  Future<void> _onAddPressed() async {
    final choice = await showModalBottomSheet<String>(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(children: [
          ListTile(
            leading: const Icon(Icons.store, color: Color(0xFF2E7D32)),
            title: const Text('Add to Marketplace'),
            onTap: () => Navigator.pop(context, 'marketplace'),
          ),
          ListTile(
            leading: const Icon(Icons.construction, color: Color(0xFF2E7D32)),
            title: const Text('Add to Rental'),
            onTap: () => Navigator.pop(context, 'rental'),
          ),
        ]),
      ),
    );

    if (choice == null) return;

    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => AddItemScreen(itemType: choice),
      ),
    );
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F5F0),
      appBar: AppBar(
        backgroundColor: const Color(0xFF2E7D32),
        title: const Text('Marketplace & Rentals'),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          tabs: const [
            Tab(text: 'Marketplace'),
            Tab(text: 'Rental'),
          ],
        ),
        actions: [
          IconButton(
            onPressed: _onAddPressed,
            icon: const Icon(Icons.add),
            tooltip: 'Add Item',
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _ItemsList(fetcher: () => _fetchItems('marketplace')),
          _ItemsList(fetcher: () => _fetchItems('rental')),
        ],
      ),
    );
  }
}

class _ItemsList extends StatelessWidget {
  final Future<List<dynamic>> Function() fetcher;
  const _ItemsList({required this.fetcher});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<dynamic>>(
      future: fetcher(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator(color: Color(0xFF2E7D32)));
        }
        final items = snapshot.data ?? [];
        if (items.isEmpty) {
          return const Center(
            child: Text('No items found', style: TextStyle(fontSize: 16, color: Colors.grey)),
          );
        }
        return ListView.builder(
          padding: const EdgeInsets.symmetric(vertical: 8),
          itemCount: items.length,
          itemBuilder: (context, index) {
            final item = items[index] as Map<String, dynamic>;
            final isRental = item['item_type'] == 'rental';
            return GestureDetector(
              onTap: isRental
                  ? () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => RentalDetailsPage(item: item),
                        ),
                      );
                    }
                  : null,
              child: Card(
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                elevation: 6,
                shadowColor: Colors.green.withOpacity(0.3),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (item['image_url'] != null)
                      ClipRRect(
                        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                        child: Image.network(
                          item['image_url'],
                          height: 180,
                          width: double.infinity,
                          fit: BoxFit.cover,
                        ),
                      )
                    else
                      Container(
                        height: 180,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                        ),
                        child: Icon(
                          isRental ? Icons.agriculture : Icons.store,
                          size: 60,
                          color: const Color(0xFF2E7D32),
                        ),
                      ),
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item['name'] ?? '',
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF2E7D32),
                            ),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Text('₹${item['price']} / ${item['per_unit'] ?? ''}',
                                  style: const TextStyle(fontSize: 16)),
                              const SizedBox(width: 16),
                              Icon(Icons.location_on, size: 18, color: Colors.grey[600]),
                              const SizedBox(width: 4),
                              Text(item['location'] ?? 'Unknown',
                                  style: const TextStyle(fontSize: 15)),
                            ],
                          ),
                          if (isRental) ...[
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                const Icon(Icons.person, size: 18, color: Colors.grey),
                                const SizedBox(width: 4),
                                Text('Operator: ${item['operator_available'] ? 'Yes' : 'No'}',
                                    style: const TextStyle(fontSize: 15)),
                              ],
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }
}

class AddItemScreen extends StatefulWidget {
  final String itemType; // 'marketplace' or 'rental'
  const AddItemScreen({Key? key, required this.itemType}) : super(key: key);

  @override
  State<AddItemScreen> createState() => _AddItemScreenState();
}

class _AddItemScreenState extends State<AddItemScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _priceController = TextEditingController();
  String _perUnit = 'hour';
  bool _operatorAvailable = false;
  File? _imageFile;
  bool _submitting = false;
  final _baseUrl = '$baseUrl/api';

  DateTime? _availabilityStart;
  DateTime? _availabilityEnd;
  List<Map<String, TimeOfDay?>> _timeSlots = [
    {'from': null, 'to': null},
  ];

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery, imageQuality: 80);
    if (picked != null) setState(() => _imageFile = File(picked.path));
  }

  Future<void> _pickDate({required bool isStart}) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: now,
      firstDate: now,
      lastDate: DateTime(now.year + 2),
      builder: (context, child) {
        return Theme(
          data: ThemeData.light().copyWith(
            colorScheme: const ColorScheme.light(
              primary: Color(0xFF2E7D32),
              onPrimary: Colors.white,
              onSurface: Colors.black,
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) {
      setState(() {
        if (isStart) _availabilityStart = picked;
        else _availabilityEnd = picked;
      });
    }
  }

  Future<void> _pickTime(int idx, String key) async {
    final picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.now(),
      builder: (context, child) {
        return Theme(
          data: ThemeData.light().copyWith(
            colorScheme: const ColorScheme.light(
              primary: Color(0xFF2E7D32),
              onPrimary: Colors.white,
              onSurface: Colors.black,
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) setState(() => _timeSlots[idx][key] = picked);
  }

  void _addTimeSlot() => setState(() => _timeSlots.add({'from': null, 'to': null}));
  void _removeTimeSlot(int idx) => setState(() { if (_timeSlots.length > 1) _timeSlots.removeAt(idx); });

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);

    final uri = Uri.parse('$_baseUrl/items/');
    final request = http.MultipartRequest('POST', uri);
    request.fields['item_type'] = widget.itemType;
    request.fields['name'] = _nameController.text.trim();
    request.fields['price'] = _priceController.text.trim();

    if (widget.itemType == 'rental') {
      request.fields['per_unit'] = _perUnit;
      request.fields['operator_available'] = _operatorAvailable.toString();
      if (_availabilityStart != null) request.fields['availability_start'] = _availabilityStart!.toIso8601String();
      if (_availabilityEnd != null) request.fields['availability_end'] = _availabilityEnd!.toIso8601String();
      request.fields['time_slots'] = jsonEncode(_timeSlots.map((slot) => {
            'from': slot['from']?.format(context),
            'to': slot['to']?.format(context),
          }).toList());
    }

    if (_imageFile != null) request.files.add(await http.MultipartFile.fromPath('image', _imageFile!.path));

    final streamed = await request.send();
    final res = await http.Response.fromStream(streamed);
    setState(() => _submitting = false);

    if (res.statusCode == 201) {
      if (!mounted) return;
      Navigator.pop(context);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed: ${res.body}')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isRental = widget.itemType == 'rental';
    return Scaffold(
      backgroundColor: const Color(0xFFF8F5F0),
      appBar: AppBar(title: Text('Add ${isRental ? 'Rental' : 'Marketplace'} Item'), backgroundColor: const Color(0xFF2E7D32)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            GestureDetector(
              onTap: _pickImage,
              child: Container(
                height: 160,
                width: double.infinity,
                decoration: BoxDecoration(color: Colors.green.shade50, borderRadius: BorderRadius.circular(12)),
                child: _imageFile == null
                    ? const Center(child: Text('Tap to pick image', style: TextStyle(color: Color(0xFF2E7D32))))
                    : ClipRRect(borderRadius: BorderRadius.circular(12), child: Image.file(_imageFile!, fit: BoxFit.cover)),
              ),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _nameController,
              decoration: const InputDecoration(
                  labelText: 'Equipment / Item Name',
                  focusedBorder: UnderlineInputBorder(borderSide: BorderSide(color: Color(0xFF2E7D32)))),
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _priceController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                  labelText: 'Price',
                  focusedBorder: UnderlineInputBorder(borderSide: BorderSide(color: Color(0xFF2E7D32)))),
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
            ),
            if (isRental) ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: _perUnit,
                decoration: const InputDecoration(labelText: 'Per'),
                items: const [
                  DropdownMenuItem(value: 'hour', child: Text('Hour')),
                  DropdownMenuItem(value: 'acre', child: Text('Acre')),
                  DropdownMenuItem(value: 'day', child: Text('Day')),
                ],
                onChanged: (val) => setState(() => _perUnit = val ?? 'hour'),
              ),
              const SizedBox(height: 12),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Operator Availability'),
                value: _operatorAvailable,
                onChanged: (v) => setState(() => _operatorAvailable = v),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(foregroundColor: const Color(0xFF2E7D32)),
                      onPressed: () => _pickDate(isStart: true),
                      child: Text(_availabilityStart == null
                          ? 'Select Start Date'
                          : 'Start: ${_availabilityStart!.toLocal().toString().split(' ')[0]}'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(foregroundColor: const Color(0xFF2E7D32)),
                      onPressed: () => _pickDate(isStart: false),
                      child: Text(_availabilityEnd == null
                          ? 'Select End Date'
                          : 'End: ${_availabilityEnd!.toLocal().toString().split(' ')[0]}'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text('Time Slots', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green.shade800)),
              ..._timeSlots.asMap().entries.map((entry) {
                final idx = entry.key;
                final slot = entry.value;
                return Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        style: OutlinedButton.styleFrom(foregroundColor: const Color(0xFF2E7D32)),
                        onPressed: () => _pickTime(idx, 'from'),
                        child: Text(slot['from'] == null ? 'From' : slot['from']!.format(context)),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: OutlinedButton(
                        style: OutlinedButton.styleFrom(foregroundColor: const Color(0xFF2E7D32)),
                        onPressed: () => _pickTime(idx, 'to'),
                        child: Text(slot['to'] == null ? 'To' : slot['to']!.format(context)),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.remove_circle, color: Colors.red),
                      onPressed: () => _removeTimeSlot(idx),
                    ),
                  ],
                );
              }).toList(),
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton.icon(
                  onPressed: _addTimeSlot,
                  icon: const Icon(Icons.add, color: Color(0xFF2E7D32)),
                  label: const Text('Add Time Slot', style: TextStyle(color: Color(0xFF2E7D32))),
                ),
              ),
            ],
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF2E7D32),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: _submitting ? null : _submit,
                child: _submitting
                    ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Text('Add Item', style: TextStyle(fontSize: 16)),
              ),
            )
          ]),
        ),
      ),
    );
  }
}

class RentalDetailsPage extends StatefulWidget {
  final Map<String, dynamic> item;
  const RentalDetailsPage({Key? key, required this.item}) : super(key: key);

  @override
  State<RentalDetailsPage> createState() => _RentalDetailsPageState();
}

class _RentalDetailsPageState extends State<RentalDetailsPage> {
  DateTime? _selectedDate;
  Set<String> _selectedSlots = {};
  bool _booking = false;
  List<dynamic> _bookedSlots = [];

  @override
  void initState() {
    super.initState();
    _fetchBookedSlots();
  }

  Future<void> _fetchBookedSlots() async {
    final token = await getToken();
    final res = await http.get(
      Uri.parse('$baseUrl/api/bookings/?item_id=${widget.item['id']}'),
      headers: {'Authorization': 'Token $token'},
    );
    if (res.statusCode == 200) {
      setState(() {
        _bookedSlots = (jsonDecode(res.body) as List<dynamic>)
            .where((b) => b['status'] == 'pending' || b['status'] == 'confirmed' || b['status'] == 'accepted')
            .toList();
      });
    }
  }

  List<DateTime> getAvailableDates() {
    if (widget.item['availability_start'] == null || widget.item['availability_end'] == null) return [];
    final start = DateTime.parse(widget.item['availability_start']);
    final end = DateTime.parse(widget.item['availability_end']);
    return List.generate(end.difference(start).inDays + 1, (i) => start.add(Duration(days: i)));
  }

  List<String> getAvailableSlots() {
    List<dynamic> slots = [];
    if (widget.item['time_slots'] != null) {
      try {
        slots = widget.item['time_slots'] is String ? jsonDecode(widget.item['time_slots']) : widget.item['time_slots'];
      } catch (_) {}
    }
    List<String> intervals = [];
    for (var slot in slots) {
      final fromStr = slot['from'];
      final toStr = slot['to'];
      if (fromStr == null || toStr == null) continue;
      final fromParts = fromStr.split(":");
      final toParts = toStr.split(":");
      if (fromParts.length < 2 || toParts.length < 2) continue;
      int fromHour = int.tryParse(fromParts[0]) ?? 0;
      int fromMin = int.tryParse(fromParts[1]) ?? 0;
      int toHour = int.tryParse(toParts[0]) ?? 0;
      int toMin = int.tryParse(toParts[1]) ?? 0;
      DateTime now = DateTime(2000, 1, 1, fromHour, fromMin);
      DateTime end = DateTime(2000, 1, 1, toHour, toMin);
      while (now.isBefore(end)) {
        final next = now.add(const Duration(minutes: 30));
        if (next.isAfter(end)) break;
        final label = "${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')} - ${next.hour.toString().padLeft(2, '0')}:${next.minute.toString().padLeft(2, '0')}";
        intervals.add(label);
        now = next;
      }
    }
    // Remove slots that are already booked for the selected date (pending or confirmed only)
    if (_selectedDate != null && _bookedSlots.isNotEmpty) {
      final booked = _bookedSlots.where((b) => b['date'] == DateFormat('yyyy-MM-dd').format(_selectedDate!)).map((b) => b['time_slot']).toSet();
      intervals = intervals.where((slot) => !booked.contains(slot)).toList();
    }
    return intervals;
  }

  Future<void> _submitBooking() async {
    if (_selectedDate == null || _selectedSlots.isEmpty) {
      print('No date or slots selected');
      return;
    }
    setState(() => _booking = true);
    try {
      final token = await getToken();
      print('Token: $token');
      final itemId = widget.item['id'].toString();
      final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate!);
      final slotsList = _selectedSlots.toList();
      final contactName = widget.item['owner_name'] ?? 'User';
      final contactPhone = widget.item['owner_phone'] ?? '0000000000';
      print('Booking data: item=$itemId, date=$dateStr, slots=$slotsList, name=$contactName, phone=$contactPhone');
      final res = await http.post(
        Uri.parse('$baseUrl/api/bookings/'),
        headers: {
          'Content-Type': 'application/json',
          if (token != null) 'Authorization': 'Token $token',
        },
        body: jsonEncode({
          'item': itemId,
          'date': dateStr,
          'time_slots': slotsList,
          'contact_name': contactName,
          'contact_phone': contactPhone,
        }),
      );
      print('Booking response: ${res.statusCode} ${res.body}');
      setState(() => _booking = false);
      if (res.statusCode == 201) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Booking Request Sent'),
            content: const Text('Your booking request has been sent to the owner.'),
            actions: [TextButton(onPressed: () {
              Navigator.pop(context);
              _fetchBookedSlots();
              setState(() {
                _selectedSlots.clear();
              });
            }, child: const Text('OK'))],
          ),
        );
      } else {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Booking Failed'),
            content: Text('Failed to book: ${res.body}'),
            actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('OK'))],
          ),
        );
      }
    } catch (e, st) {
      print('Booking exception: $e\n$st');
      setState(() => _booking = false);
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Error'),
          content: Text('An error occurred: $e'),
          actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('OK'))],
        ),
      );
    }
  }

  void _callOwner(String phone) async {
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
    final item = widget.item;
    List<DateTime> availableDates = getAvailableDates();
    List<String> availableSlots = getAvailableSlots();

    return Scaffold(
      backgroundColor: const Color(0xFFF8F5F0),
      appBar: AppBar(title: Text(item['name'] ?? 'Rental Details'), backgroundColor: const Color(0xFF2E7D32)),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (item['image_url'] != null)
              Image.network(item['image_url'], width: double.infinity, height: 220, fit: BoxFit.cover)
            else
              Container(
                height: 220,
                color: Colors.green.shade50,
                child: const Icon(Icons.agriculture, size: 80, color: Color(0xFF2E7D32)),
              ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item['name'] ?? '', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF2E7D32))),
                  const SizedBox(height: 8),
                  Text('₹${item['price']} / ${item['per_unit'] ?? ''}', style: const TextStyle(fontSize: 18)),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(Icons.location_on, size: 18, color: Colors.grey[600]),
                      const SizedBox(width: 4),
                      Text(item['location'] ?? 'Unknown', style: const TextStyle(fontSize: 16)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(Icons.person, size: 18, color: Colors.grey),
                      const SizedBox(width: 4),
                      Text('Operator: ${item['operator_available'] ? 'Yes' : 'No'}', style: const TextStyle(fontSize: 16)),
                    ],
                  ),
                  const Divider(height: 32),
                  if (availableDates.isNotEmpty) ...[
                    const Text('Select Date:', style: TextStyle(fontWeight: FontWeight.bold)),
                    SizedBox(
                      height: 60,
                      child: ListView.builder(
                        scrollDirection: Axis.horizontal,
                        itemCount: availableDates.length,
                        itemBuilder: (context, idx) {
                          final date = availableDates[idx];
                          final selected = _selectedDate != null && DateUtils.isSameDay(_selectedDate, date);
                          return Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 4),
                            child: ChoiceChip(
                              label: Text(DateFormat('MMM d').format(date)),
                              selected: selected,
                              onSelected: (_) => setState(() {
                                _selectedDate = date;
                                _selectedSlots.clear();
                              }),
                              selectedColor: const Color(0xFF2E7D32),
                              labelStyle: TextStyle(color: selected ? Colors.white : Colors.black),
                            ),
                          );
                        },
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                  if (_selectedDate != null && availableSlots.isNotEmpty) ...[
                    const Text('Select Time Slot(s):', style: TextStyle(fontWeight: FontWeight.bold)),
                    Wrap(
                      spacing: 8,
                      children: availableSlots.map((slot) {
                        final selected = _selectedSlots.contains(slot);
                        return ChoiceChip(
                          label: Text(slot),
                          selected: selected,
                          onSelected: (_) => setState(() {
                            if (selected) {
                              _selectedSlots.remove(slot);
                            } else {
                              _selectedSlots.add(slot);
                            }
                          }),
                          selectedColor: const Color(0xFF2E7D32),
                          labelStyle: TextStyle(color: selected ? Colors.white : Colors.black),
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 16),
                  ],
                  if (_selectedDate != null && _selectedSlots.isNotEmpty)
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF2E7D32),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                        ),
                        onPressed: _booking ? null : _submitBooking,
                        child: _booking
                            ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : const Text('Book Slot(s)', style: TextStyle(fontSize: 16)),
                      ),
                    ),
                  const Divider(height: 32),
                  const Text('Owner Information', style: TextStyle(fontWeight: FontWeight.bold)),
                  Text('Name: ${item['owner_name'] ?? 'N/A'}'),
                  Row(
                    children: [
                      const Icon(Icons.phone, size: 18, color: Colors.grey),
                      const SizedBox(width: 4),
                      Text(item['owner_phone'] ?? 'N/A', style: const TextStyle(fontSize: 16)),
                      const SizedBox(width: 8),
                      IconButton(
                        icon: const Icon(Icons.call, color: Color(0xFF2E7D32)),
                        tooltip: 'Call Owner',
                        onPressed: () => _callOwner(item['owner_phone'] ?? ''),
                      ),
                    ],
                  ),
                  Text('Address: ${item['owner_address'] ?? 'N/A'}'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
