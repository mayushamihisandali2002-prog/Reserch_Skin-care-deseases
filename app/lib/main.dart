import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:provider/provider.dart';
import 'utils/app_styles.dart';
import 'utils/app_theme.dart';
import 'services/supabase_service.dart';

import 'screens/login_screen.dart';
import 'screens/home_container.dart';
import 'screens/onboarding_screen.dart';
import 'screens/journey_setup_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Optimize system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(statusBarColor: Colors.transparent),
  );

  // Configure Google Fonts to allow fetching from network but with fallbacks
  GoogleFonts.config.allowRuntimeFetching = true;

  // Run app immediately with splash, initialize in background
  runApp(
    ChangeNotifierProvider(
      create: (_) => ThemeProvider(),
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);

    return MaterialApp(
      title: 'Skin Care Assistant',
      debugShowCheckedModeBanner: false,
      themeMode: themeProvider.themeMode,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      home: const AuthWrapper(),
      routes: {
        '/onboarding': (context) => const OnboardingScreen(),
        '/journey-setup': (context) => const JourneySetupScreen(),
        '/home': (context) => const HomeContainer(),
      },
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
  bool _needsOnboarding = false;

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

  Future<void> _checkAuthState() async {
    final isLoggedIn = SupabaseService.isLoggedIn;
    bool needsOnboarding = false;

    if (isLoggedIn) {
      final profile = await SupabaseService.getProfile();
      // If skin_type is not set, we assume they need onboarding
      needsOnboarding = profile == null || profile['skin_type'] == null;
    }

    if (mounted) {
      setState(() {
        _isLoggedIn = isLoggedIn;
        _needsOnboarding = needsOnboarding;
        _isInitializing = false;
      });
    }
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
        backgroundColor: context.clrBackground,
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
                  color: context.clrTextMain,
                ),
              ),
              const SizedBox(height: 16),
              CircularProgressIndicator(color: AppColors.primary),
            ],
          ),
        ),
      );
    }

    if (_isLoggedIn) {
      return _needsOnboarding
          ? const OnboardingScreen()
          : const HomeContainer();
    }
    return const LoginScreen();
  }
}
