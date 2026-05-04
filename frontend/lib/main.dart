import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_web_plugins/url_strategy.dart';
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
  usePathUrlStrategy();

  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
      systemNavigationBarColor: Colors.white,
    ),
  );

  GoogleFonts.config.allowRuntimeFetching = true;

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SkinAI – Clinical Skin Care',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.light,
      theme: AppTheme.lightTheme,
      home: const AuthWrapper(initialIndex: 0),
      routes: {
        '/onboarding': (context) => const OnboardingScreen(),
        '/journey-setup': (context) => const JourneySetupScreen(),
        '/home': (context) => const AuthWrapper(initialIndex: 0),
        '/AIchat': (context) => const AuthWrapper(initialIndex: 1),
        '/Scan': (context) => const AuthWrapper(initialIndex: 2),
        '/Skincare': (context) => const AuthWrapper(initialIndex: 3),
        '/Severity': (context) => const AuthWrapper(initialIndex: 4),
      },
    );
  }
}

class AuthWrapper extends StatefulWidget {
  final int initialIndex;

  const AuthWrapper({super.key, this.initialIndex = 0});

  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper>
    with SingleTickerProviderStateMixin {
  bool _isInitializing = true;
  bool _isLoggedIn = false;
  bool _needsOnboarding = false;
  String? _initializationError;
  late AnimationController _animController;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _fadeAnim = CurvedAnimation(parent: _animController, curve: Curves.easeOut);
    _animController.forward();
    _initializeApp();
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  Future<void> _initializeApp() async {
    try {
      await SupabaseService.initialize();
      if (mounted) {
        _checkAuthState();
        _listenToAuthChanges();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _initializationError = e.toString();
          _isInitializing = false;
        });
      }
    }
  }

  Future<void> _checkAuthState() async {
    final isLoggedIn = SupabaseService.isLoggedIn;
    bool needsOnboarding = false;

    if (isLoggedIn) {
      try {
        final profile = await SupabaseService.getProfile();
        final displayName =
            (profile?['full_name'] ??
                    SupabaseService.currentUser?.userMetadata?['full_name'] ??
                    '')
                .toString()
                .trim();
        needsOnboarding = displayName.isEmpty;
      } catch (e) {
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
        if (event == AuthChangeEvent.signedIn ||
            event == AuthChangeEvent.tokenRefreshed ||
            event == AuthChangeEvent.initialSession) {
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
      return _buildSplashScreen();
    }

    if (_initializationError != null) {
      return _buildErrorScreen();
    }

    if (_isLoggedIn) {
      _cleanRouteHash();
      return _needsOnboarding
          ? const OnboardingScreen()
          : HomeContainer(initialIndex: widget.initialIndex);
    }
    return const LoginScreen();
  }

  void _cleanRouteHash() {
    final routeName = ModalRoute.of(context)?.settings.name;
    if (routeName == null || routeName.isEmpty) return;
    SystemNavigator.routeInformationUpdated(uri: Uri.parse(routeName), replace: true);
  }

  Widget _buildSplashScreen() {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF0F4C5C), Color(0xFF082D36)],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: FadeTransition(
              opacity: _fadeAnim,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.15),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.3),
                        width: 2,
                      ),
                    ),
                    child: const Icon(
                      Icons.health_and_safety_rounded,
                      size: 64,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 28),
                  const Text(
                    'SkinAI',
                    style: TextStyle(
                      fontSize: 36,
                      fontWeight: FontWeight.w900,
                      color: Colors.white,
                      letterSpacing: -1,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Clinical Skin Care Assistant',
                    style: TextStyle(
                      fontSize: 15,
                      color: Colors.white.withValues(alpha: 0.7),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 48),
                  SizedBox(
                    width: 36,
                    height: 36,
                    child: CircularProgressIndicator(
                      color: Colors.white.withValues(alpha: 0.8),
                      strokeWidth: 2.5,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildErrorScreen() {
    return Scaffold(
      backgroundColor: const Color(0xFFF1F5F7),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Container(
                padding: const EdgeInsets.all(28),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(28),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.08),
                      blurRadius: 30,
                      offset: const Offset(0, 12),
                    ),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.warning.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: const Icon(
                        Icons.warning_amber_rounded,
                        size: 32,
                        color: AppColors.warning,
                      ),
                    ),
                    const SizedBox(height: 20),
                    const Text(
                      'Configuration Required',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                        color: Color(0xFF10252D),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      _initializationError!,
                      style: const TextStyle(
                        fontSize: 14,
                        color: Color(0xFF5E737C),
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: 20),
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0F4C5C).withValues(alpha: 0.05),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const SelectableText(
                        'flutter run -d chrome\n  --dart-define=SUPABASE_URL=...\n  --dart-define=SUPABASE_ANON_KEY=...',
                        style: TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 12,
                          color: Color(0xFF0F4C5C),
                        ),
                      ),
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
