import 'package:shared_preferences/shared_preferences.dart';

const String baseUrl = 'https://m5df48wm-8000.inc1.devtunnels.ms';

Future<String?> getToken() async {
  final prefs = await SharedPreferences.getInstance();
  return prefs.getString('token');
}
