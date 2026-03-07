import 'package:flutter/material.dart';

extension ThemeExtension on BuildContext {
  ThemeData get theme => Theme.of(this);
  bool get isDarkMode => theme.brightness == Brightness.dark;
  ColorScheme get colorScheme => theme.colorScheme;

  Color get clrSurfaceGlass => isDarkMode ? const Color(0x99161B22) : const Color(0x99FFFFFF).withValues(alpha: 0.9);
  Color get clrSurface => colorScheme.surface;
  Color get clrBackgroundAlt => isDarkMode ? const Color(0xFF0D1117) : const Color(0xFFF1F5F7);
  Color get clrBackground => colorScheme.surfaceContainerHighest.withValues(alpha: 0.1); 
  // Using a more dynamic background
  Color get clrBackgroundReal => theme.scaffoldBackgroundColor;
  Color get clrTextMain => colorScheme.onSurface;
  Color get clrTextSec => colorScheme.onSurfaceVariant;
  Color get clrBorder => colorScheme.outline;
}

class AppColors {
  // Primary: Sophisticated deep teal/emerald
  static const Color primary = Color(0xFF0F4C5C);
  static const Color primaryLight = Color(0xFF236B7D);
  static const Color primaryDark = Color(0xFF082D36);

  // Accents: Vibrant but balanced
  static const Color secondary = Color(0xFFE36414); // Vibrant sunset orange
  static const Color accent = Color(0xFF5F0F40); // Deep wine
  static const Color highlight = Color(0xFF9B2226); // Rich red

  // Fixed colors for legacy support during refactor
  static const Color surface = Color(0xFFFFFFFF);
  static const Color background = Color(0xFFF8FBFC);
  static const Color textMain = Color(0xFF10252D);
  static const Color textSecondary = Color(0xFF5E737C);
  static const Color border = Color(0xFFE1E8EB);

  // Status
  static const Color success = Color(0xFF1B998B);
  static const Color warning = Color(0xFFFB8500);
  static const Color error = Color(0xFFD62828);
}

class AppTextStyles {
  static TextStyle heading(BuildContext context) => TextStyle(
    fontSize: 26,
    fontWeight: FontWeight.w700,
    letterSpacing: -0.3,
    color: context.clrTextMain,
  );

  static TextStyle subHeading(BuildContext context) => TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w700,
    letterSpacing: -0.1,
    color: context.clrTextMain,
  );

  static TextStyle body(BuildContext context) => TextStyle(
    fontSize: 14,
    height: 1.5,
    color: context.clrTextSec,
  );

  static TextStyle bodyStrong(BuildContext context) => TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w600,
    color: context.clrTextMain,
  );

  static TextStyle caption(BuildContext context) => TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w500,
    color: context.clrTextSec,
  );
}

class AppGradients {
  static const LinearGradient hero = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF0F4C5C), Color(0xFF236B7D)],
  );

  static const LinearGradient premium = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF0F4C5C), Color(0xFF5F0F40)],
  );

  static LinearGradient page(BuildContext context) => LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [
      context.theme.scaffoldBackgroundColor,
      context.clrBackgroundAlt,
    ],
  );

  static LinearGradient glass(BuildContext context) => LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      context.clrSurfaceGlass.withValues(alpha: 0.8),
      context.clrSurfaceGlass.withValues(alpha: 0.4),
    ],
  );
}

class AppDecor {
  static BoxDecoration softCard(
    BuildContext context, {
    Color? color,
    Color? borderColor,
    double radius = 24.0,
    bool showBorder = true,
  }) {
    return BoxDecoration(
      color: color ?? context.clrSurface,
      borderRadius: BorderRadius.circular(radius),
      border: showBorder
          ? Border.all(
              color: borderColor ?? context.clrBorder.withValues(alpha: 0.6),
            )
          : null,
      boxShadow: [
        BoxShadow(
          color: context.isDarkMode 
              ? Colors.black.withValues(alpha: 0.3) 
              : const Color(0xFF10252D).withValues(alpha: 0.06),
          blurRadius: 24,
          offset: const Offset(0, 12),
        ),
      ],
    );
  }

  static BoxDecoration glassCard(BuildContext context, {double radius = 24.0}) {
    return BoxDecoration(
      borderRadius: BorderRadius.circular(radius),
      gradient: AppGradients.glass(context),
      border: Border.all(color: context.clrBorder.withValues(alpha: 0.2)),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.05),
          blurRadius: 15,
          spreadRadius: 2,
        ),
      ],
    );
  }
}
