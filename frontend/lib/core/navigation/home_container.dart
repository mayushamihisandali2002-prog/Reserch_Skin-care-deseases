import 'package:app/core/overview/presentation/dashboard_screen.dart';
import 'package:app/components/conversational_diagnosis_assistant/presentation/chat_screen.dart';
import 'package:app/components/multimodal_image_audio_diagnosis/presentation/instruction_screen.dart';
import 'package:app/components/severity_assessment_tracking/presentation/severity_screen.dart';
import 'package:app/components/skin_type_skincare_recommendation/presentation/skin_care_screen.dart';
import 'package:app/utils/app_styles.dart';
import 'package:flutter/material.dart';

class HomeContainer extends StatefulWidget {
  const HomeContainer({super.key});

  @override
  State<HomeContainer> createState() => _HomeContainerState();
}

class _HomeContainerState extends State<HomeContainer> {
  int _currentIndex = 0;

  void _selectTab(int index) {
    if (!mounted) return;
    setState(() => _currentIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      DashboardScreen(onSelectTab: _selectTab),
      const InstructionScreen(),
      const ChatScreen(),
      const SkinCareScreen(),
      const SeverityScreen(),
    ];

    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: screens),
      bottomNavigationBar: Container(
        height: 92,
        decoration: BoxDecoration(
          color: context.clrSurface,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 18,
              offset: const Offset(0, -6),
            ),
          ],
        ),
        child: SafeArea(
          top: false,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1080),
              child: NavigationBarTheme(
                data: NavigationBarThemeData(
                  indicatorColor: AppColors.primary.withValues(alpha: 0.12),
                  labelTextStyle: WidgetStateProperty.resolveWith((states) {
                    if (states.contains(WidgetState.selected)) {
                      return const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w800,
                        color: AppColors.primary,
                      );
                    }
                    return TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                      color: context.clrTextSec,
                    );
                  }),
                  iconTheme: WidgetStateProperty.resolveWith((states) {
                    if (states.contains(WidgetState.selected)) {
                      return const IconThemeData(
                        color: AppColors.primary,
                        size: 26,
                      );
                    }
                    return IconThemeData(color: context.clrTextSec, size: 24);
                  }),
                ),
                child: NavigationBar(
                  elevation: 0,
                  backgroundColor: Colors.transparent,
                  height: 74,
                  selectedIndex: _currentIndex,
                  onDestinationSelected: _selectTab,
                  destinations: const [
                    NavigationDestination(
                      icon: Icon(Icons.home_rounded),
                      selectedIcon: Icon(Icons.home_rounded),
                      label: 'Home',
                    ),
                    NavigationDestination(
                      icon: Icon(Icons.auto_fix_high_rounded),
                      selectedIcon: Icon(Icons.auto_fix_high_rounded),
                      label: 'Smart Scan',
                    ),
                    NavigationDestination(
                      icon: Icon(Icons.forum_rounded),
                      selectedIcon: Icon(Icons.forum_rounded),
                      label: 'AI Chat',
                    ),
                    NavigationDestination(
                      icon: Icon(Icons.spa_rounded),
                      selectedIcon: Icon(Icons.spa_rounded),
                      label: 'Skin Care',
                    ),
                    NavigationDestination(
                      icon: Icon(Icons.speed_rounded),
                      selectedIcon: Icon(Icons.speed_rounded),
                      label: 'Severity',
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
