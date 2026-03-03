import 'package:flutter/material.dart';

class AppColors {
  static const Color primary = Color(0xFF1F7A8C);
  static const Color primaryDark = Color(0xFF145563);
  static const Color secondary = Color(0xFFF4A259);
  static const Color accent = Color(0xFF6EB5A9);

  static const Color background = Color(0xFFF3F6F8);
  static const Color backgroundAlt = Color(0xFFEAF0F3);
  static const Color surface = Color(0xFFFFFFFF);

  static const Color textMain = Color(0xFF132A36);
  static const Color textSecondary = Color(0xFF5B6E78);
  static const Color border = Color(0xFFD9E3E8);

  static const Color success = Color(0xFF2E9B67);
  static const Color warning = Color(0xFFC27B2A);
  static const Color error = Color(0xFFD64550);
}

class AppTextStyles {
  static const TextStyle heading = TextStyle(
    fontSize: 26,
    fontWeight: FontWeight.w700,
    letterSpacing: -0.3,
    color: AppColors.textMain,
  );

  static const TextStyle subHeading = TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w700,
    letterSpacing: -0.1,
    color: AppColors.textMain,
  );

  static const TextStyle body = TextStyle(
    fontSize: 14,
    height: 1.5,
    color: AppColors.textSecondary,
  );

  static const TextStyle bodyStrong = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w600,
    color: AppColors.textMain,
  );

  static const TextStyle caption = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w500,
    color: AppColors.textSecondary,
  );
}

class AppGradients {
  static const LinearGradient hero = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF246A77), Color(0xFF1E4D57)],
  );

  static const LinearGradient page = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0xFFF6FAFC), Color(0xFFEFF4F7)],
  );
}

class AppDecor {
  static BoxDecoration softCard({
    Color color = AppColors.surface,
    Color borderColor = AppColors.border,
  }) {
    return BoxDecoration(
      color: color,
      borderRadius: BorderRadius.circular(18),
      border: Border.all(color: borderColor),
      boxShadow: const [
        BoxShadow(
          color: Color(0x140C1B22),
          blurRadius: 16,
          offset: Offset(0, 8),
        ),
      ],
    );
  }
}
