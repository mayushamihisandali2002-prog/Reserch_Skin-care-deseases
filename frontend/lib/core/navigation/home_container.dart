import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:app/components/conversational_diagnosis_assistant/presentation/chat_screen.dart';
import 'package:app/components/multimodal_image_audio_diagnosis/presentation/instruction_screen.dart';
import 'package:app/components/severity_assessment_tracking/presentation/severity_screen.dart';
import 'package:app/components/skin_type_skincare_recommendation/presentation/skin_care_screen.dart';
import 'package:app/core/overview/presentation/dashboard_screen.dart';
import 'package:app/utils/app_styles.dart';

class HomeContainer extends StatefulWidget {
  final int initialIndex;

  const HomeContainer({super.key, this.initialIndex = 0});

  @override
  State<HomeContainer> createState() => _HomeContainerState();
}

class _HomeContainerState extends State<HomeContainer> {
  int _currentIndex = 0;

  static const _paths = ['/home', '/AIchat', '/Scan', '/Skincare', '/Severity'];

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex.clamp(0, 4);
  }

  void _selectTab(int index) {
    if (!mounted) return;
    final path = _paths[index];
    if (ModalRoute.of(context)?.settings.name == path) {
      setState(() => _currentIndex = index);
      SystemNavigator.routeInformationUpdated(uri: Uri.parse(path), replace: true);
      return;
    }
    SystemNavigator.routeInformationUpdated(uri: Uri.parse(path), replace: true);
    Navigator.of(context).pushReplacementNamed(path);
  }

  static const _navItems = [
    _NavItem(
      icon: Icons.home_outlined,
      activeIcon: Icons.home_rounded,
      label: 'Home',
    ),
    _NavItem(
      icon: Icons.forum_outlined,
      activeIcon: Icons.forum_rounded,
      label: 'AI Chat',
    ),
    _NavItem(
      icon: Icons.auto_fix_high_outlined,
      activeIcon: Icons.auto_fix_high_rounded,
      label: 'Scan',
    ),
    _NavItem(
      icon: Icons.spa_outlined,
      activeIcon: Icons.spa_rounded,
      label: 'Skin Care',
    ),
    _NavItem(
      icon: Icons.speed_outlined,
      activeIcon: Icons.speed_rounded,
      label: 'Severity',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final screens = [
      DashboardScreen(onSelectTab: _selectTab),
      const ChatScreen(),
      const InstructionScreen(),
      const SkinCareScreen(),
      const SeverityScreen(),
    ];

    final isMobileWidth = MediaQuery.of(context).size.width < 600;

    return Scaffold(
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 220),
        switchInCurve: Curves.easeInOut,
        child: IndexedStack(
          key: ValueKey(_currentIndex),
          index: _currentIndex,
          children: screens,
        ),
      ),
      bottomNavigationBar: _buildBottomNav(context, isMobileWidth),
    );
  }

  Widget _buildBottomNav(BuildContext context, bool isMobile) {
    return Container(
      decoration: BoxDecoration(
        color: context.clrSurface,
        border: Border(
          top: BorderSide(
            color: context.clrBorder.withValues(alpha: 0.35),
            width: 1,
          ),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 20,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: EdgeInsets.symmetric(
            horizontal: isMobile ? 4 : 24,
            vertical: 6,
          ),
          child: Row(
            children: List.generate(_navItems.length, (index) {
              final item = _navItems[index];
              final isActive = index == _currentIndex;
              return Expanded(
                child: _buildNavItem(
                  context,
                  item,
                  index,
                  isActive,
                  isPrimary: index == 2,
                ),
              );
            }),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(
    BuildContext context,
    _NavItem item,
    int index,
    bool isActive, {
    bool isPrimary = false,
  }) {
    if (isPrimary) {
      // Special floating action style for the Scan button
      return GestureDetector(
        onTap: () => _selectTab(index),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.primary, AppColors.primaryDark],
                ),
                borderRadius: BorderRadius.circular(28),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withValues(alpha: 0.4),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    isActive ? item.activeIcon : item.icon,
                    color: Colors.white,
                    size: 22,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    item.label,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 2),
          ],
        ),
      );
    }

    return GestureDetector(
      onTap: () => _selectTab(index),
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: isActive
                    ? AppColors.primary.withValues(alpha: 0.12)
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                isActive ? item.activeIcon : item.icon,
                color: isActive ? AppColors.primary : context.clrTextSec,
                size: 22,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              item.label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: isActive ? FontWeight.w800 : FontWeight.w500,
                color: isActive ? AppColors.primary : context.clrTextSec,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NavItem {
  final IconData icon;
  final IconData activeIcon;
  final String label;
  const _NavItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
  });
}
