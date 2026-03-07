import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

class AppTheme {
  // Shared brand colors
  static const Color primary = Color(0xFF0F4C5C);
  static const Color secondary = Color(0xFFE36414);
  static const Color accent = Color(0xFF5F0F40);
  static const Color highlight = Color(0xFF9B2226);
  static const Color success = Color(0xFF1B998B);
  static const Color warning = Color(0xFFFB8500);
  static const Color error = Color(0xFFD62828);

  // Light Mode Colors
  static const Color lightBackground = Color(0xFFF8FBFC);
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightTextMain = Color(0xFF10252D);
  static const Color lightTextSec = Color(0xFF5E737C);
  static const Color lightBorder = Color(0xFFE1E8EB);

  // Dark Mode Colors
  static const Color darkBackground = Color(0xFF0D1117);
  static const Color darkSurface = Color(0xFF161B22);
  static const Color darkTextMain = Color(0xFFE6EDF3);
  static const Color darkTextSec = Color(0xFF848D97);
  static const Color darkBorder = Color(0xFF30363D);

  static TextTheme _baseTextTheme(Brightness brightness) {
    final base = kIsWeb ? Typography.material2021().black : GoogleFonts.outfitTextTheme();
    final textColor = brightness == Brightness.light ? lightTextMain : darkTextMain;
    return base.apply(
      bodyColor: textColor,
      displayColor: textColor,
      fontFamily: kIsWeb ? 'Segoe UI, Roboto, sans-serif' : null,
    );
  }

  static ThemeData get lightTheme {
    return ThemeData(
      brightness: Brightness.light,
      primaryColor: primary,
      scaffoldBackgroundColor: lightBackground,
      colorScheme: const ColorScheme.light(
        primary: primary,
        secondary: secondary,
        surface: lightSurface,
        error: error,
        onSurface: lightTextMain,
        onSurfaceVariant: lightTextSec,
        outline: lightBorder,
      ),
      textTheme: _baseTextTheme(Brightness.light),
      appBarTheme: AppBarTheme(
        backgroundColor: lightSurface,
        foregroundColor: lightTextMain,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.outfit(
          color: lightTextMain,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
      dividerColor: lightBorder,
      cardColor: lightSurface,
      useMaterial3: true,
    );
  }

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      primaryColor: primary,
      scaffoldBackgroundColor: darkBackground,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: secondary,
        surface: darkSurface,
        error: error,
        onSurface: darkTextMain,
        onSurfaceVariant: darkTextSec,
        outline: darkBorder,
      ),
      textTheme: _baseTextTheme(Brightness.dark),
      appBarTheme: AppBarTheme(
        backgroundColor: darkSurface,
        foregroundColor: darkTextMain,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.outfit(
          color: darkTextMain,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
      dividerColor: darkBorder,
      cardColor: darkSurface,
      useMaterial3: true,
    );
  }
}

class ThemeProvider extends ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.system;

  ThemeMode get themeMode => _themeMode;

  bool get isDarkMode {
    if (_themeMode == ThemeMode.system) {
      return WidgetsBinding.instance.platformDispatcher.platformBrightness == Brightness.dark;
    }
    return _themeMode == ThemeMode.dark;
  }

  void toggleTheme(bool isOn) {
    _themeMode = isOn ? ThemeMode.dark : ThemeMode.light;
    notifyListeners();
  }

  void setThemeMode(ThemeMode mode) {
    _themeMode = mode;
    notifyListeners();
  }
}
