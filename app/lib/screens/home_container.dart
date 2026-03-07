import 'package:flutter/material.dart';

import '../utils/app_styles.dart';
import 'chat_screen.dart';
import 'dashboard_screen.dart';
import 'instruction_screen.dart';
import 'severity_screen.dart';
import 'skin_care_screen.dart';

class HomeContainer extends StatefulWidget {
  const HomeContainer({super.key});

  @override
  State<HomeContainer> createState() => _HomeContainerState();
}

class _HomeContainerState extends State<HomeContainer> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    DashboardScreen(),
    InstructionScreen(),
    SkinCareScreen(),
    SeverityScreen(),
    ChatScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: Container(
        height: 85,
        decoration: BoxDecoration(
          color: context.clrSurface,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 10,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: NavigationBarTheme(
          data: NavigationBarThemeData(
            indicatorColor: AppColors.primary.withValues(alpha: 0.1),
            labelTextStyle: WidgetStateProperty.resolveWith((states) {
              if (states.contains(WidgetState.selected)) {
                return TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: AppColors.primary);
              }
              return TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: context.clrTextSec);
            }),
            iconTheme: WidgetStateProperty.resolveWith((states) {
              if (states.contains(WidgetState.selected)) {
                return const IconThemeData(color: AppColors.primary, size: 26);
              }
              return IconThemeData(color: context.clrTextSec, size: 24);
            }),
          ),
          child: NavigationBar(
            elevation: 0,
            backgroundColor: Colors.transparent,
            height: 70,
            selectedIndex: _currentIndex,
            onDestinationSelected: (index) {
              setState(() => _currentIndex = index);
            },
            destinations: const [
              NavigationDestination(
                icon: Icon(Icons.grid_view_rounded),
                selectedIcon: Icon(Icons.grid_view_rounded),
                label: 'Dashboard',
              ),
              NavigationDestination(
                icon: Icon(Icons.auto_fix_high_rounded),
                selectedIcon: Icon(Icons.auto_fix_high_rounded),
                label: 'Diagnose',
              ),
              NavigationDestination(
                icon: Icon(Icons.spa_rounded),
                selectedIcon: Icon(Icons.spa_rounded),
                label: 'Care',
              ),
              NavigationDestination(
                icon: Icon(Icons.speed_rounded),
                selectedIcon: Icon(Icons.speed_rounded),
                label: 'Severity',
              ),
              NavigationDestination(
                icon: Icon(Icons.forum_rounded),
                selectedIcon: Icon(Icons.forum_rounded),
                label: 'AI Chat',
              ),
            ],
          ),
        ),
      ),
    );
  }
}
