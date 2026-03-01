import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'utils/app_styles.dart';
import 'services/supabase_service.dart';

import 'screens/login_screen.dart';
import 'screens/home_container.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Optimize system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(statusBarColor: Colors.transparent),
  );

  // Configure Google Fonts to allow fetching from network but with fallbacks
  GoogleFonts.config.allowRuntimeFetching = true;

  // Run app immediately with splash, initialize in background
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Skin Care Assistant',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.primary,
          primary: AppColors.primary,
          secondary: AppColors.secondary,
          background: AppColors.background,
          surface: AppColors.surface,
        ),
        useMaterial3: true,
        // Use system fonts as fallback to avoid network font loading issues
        textTheme: kIsWeb
            ? Typography.material2021().black.apply(
                fontFamily: 'Segoe UI, Roboto, sans-serif',
              )
            : GoogleFonts.outfitTextTheme(),
        scaffoldBackgroundColor: AppColors.background,
      ),
      home: const AuthWrapper(),
    );
  }
}

/// Wrapper widget that handles authentication state
class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key});

  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  bool _isInitializing = true;
  bool _isLoggedIn = false;

  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    // Initialize Supabase in background
    await SupabaseService.initialize();

    if (mounted) {
      _checkAuthState();
      _listenToAuthChanges();
    }
  }

  void _checkAuthState() {
    setState(() {
      _isLoggedIn = SupabaseService.isLoggedIn;
      _isInitializing = false;
    });
  }

  void _listenToAuthChanges() {
    SupabaseService.authStateChanges.listen((data) {
      final AuthChangeEvent event = data.event;
      if (mounted) {
        setState(() {
          _isLoggedIn =
              event == AuthChangeEvent.signedIn ||
              (event != AuthChangeEvent.signedOut &&
                  SupabaseService.isLoggedIn);
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isInitializing) {
      return Scaffold(
        backgroundColor: AppColors.background,
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.health_and_safety, size: 80, color: AppColors.primary),
              const SizedBox(height: 24),
              Text(
                'Skin Care Assistant',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textMain,
                ),
              ),
              const SizedBox(height: 16),
              CircularProgressIndicator(color: AppColors.primary),
            ],
          ),
        ),
      );
    }

    return _isLoggedIn ? const HomeContainer() : const LoginScreen();
  }
}
