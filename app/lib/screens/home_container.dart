import 'package:flutter/material.dart';
// We can use IconData if SVG assets aren't ready
import '../utils/app_styles.dart';
import 'dashboard_screen.dart';
import 'analyze_screen.dart';
import 'chat_screen.dart';
import 'instruction_screen.dart';

class HomeContainer extends StatefulWidget {
  const HomeContainer({super.key});

  @override
  State<HomeContainer> createState() => _HomeContainerState();
}

class _HomeContainerState extends State<HomeContainer> {
  int _currentIndex = 0;

  // Lazy-load screens to improve startup performance
  Widget _getScreen(int index) {
    switch (index) {
      case 0:
        return const DashboardScreen();
      case 1:
        return const AnalyzeScreen();
      case 2:
        return const ChatScreen();
      default:
        return const DashboardScreen();
    }
  }

  void _onTabTapped(int index) {
    setState(() {
      _currentIndex = index;
    });
  }

  void _openScanner() {
    Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (context) => const InstructionScreen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: true,
      body: _getScreen(_currentIndex),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: _onTabTapped,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.analytics_outlined),
            selectedIcon: Icon(Icons.analytics),
            label: 'Analyze',
          ),
          NavigationDestination(
            icon: Icon(Icons.chat_bubble_outline),
            selectedIcon: Icon(Icons.chat_bubble),
            label: 'Chat',
          ),
        ],
      ),
      // Only show "New Scan" button on Home and Analyze tabs, NOT on Chat tab
      floatingActionButton: _currentIndex != 2
          ? FloatingActionButton.extended(
              onPressed: _openScanner,
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              icon: const Icon(Icons.camera_alt),
              label: const Text('New Scan'),
            )
          : null,
    );
  }
}
