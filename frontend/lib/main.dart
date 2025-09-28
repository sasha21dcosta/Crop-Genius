import 'package:flutter/material.dart';
import 'login.dart';
import 'marketplace.dart';

void main() => runApp(MaterialApp(
  home: LoginPage(),
  routes: {
    '/marketplace': (context) => const MarketplaceScreen(),
  },
));
