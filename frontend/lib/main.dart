import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:app/components/severity_assessment_tracking/presentation/journey_setup_screen.dart';
import 'package:app/core/auth/presentation/login_screen.dart';
import 'package:app/core/auth/presentation/onboarding_screen.dart';
import 'package:app/core/navigation/home_container.dart';
import 'package:app/services/supabase_service.dart';
import 'package:app/utils/app_styles.dart';
import 'package:app/utils/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Optimize system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(statusBarColor: Colors.transparent),
  );

  // Configure Google Fonts to allow fetching from network but with fallbacks
  GoogleFonts.config.allowRuntimeFetching = true;

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Skin Care Assistant',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.light,
      theme: AppTheme.lightTheme,
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
      try {
        final profile = await SupabaseService.getProfile();
        final displayName = (profile?['full_name'] ??
                SupabaseService.currentUser?.userMetadata?['full_name'] ??
                '')
            .toString()
            .trim();
        needsOnboarding = displayName.isEmpty;
      } catch (e) {
        // If profile fetch fails, do not force onboarding loop
        needsOnboarding = false;
      }
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
        if (event == AuthChangeEvent.signedIn || event == AuthChangeEvent.tokenRefreshed) {
           _checkAuthState();
        } else if (event == AuthChangeEvent.signedOut) {
           setState(() {
             _isLoggedIn = false;
             _needsOnboarding = false;
           });
        }
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
