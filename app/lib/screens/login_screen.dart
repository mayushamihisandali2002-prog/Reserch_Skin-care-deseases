import 'package:flutter/material.dart';
import '../utils/app_styles.dart';
import 'home_container.dart';
import 'register_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;

  void _login() async {
    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 1)); // Mock login
    if (mounted) {
       setState(() => _isLoading = false);
       // Navigate to HomeContainer
       Navigator.of(context).pushReplacement(
         MaterialPageRoute(builder: (context) => const HomeContainer()),
       );
    }
  }

  @override
  Widget build(BuildContext context) {
     return Scaffold(
       body: Container(
         decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [AppColors.background, Colors.white],
            ),
         ),
         child: Center(
           child: SingleChildScrollView(
             padding: const EdgeInsets.all(24),
             child: Column(
               mainAxisAlignment: MainAxisAlignment.center,
               crossAxisAlignment: CrossAxisAlignment.stretch,
               children: [
                 const Icon(Icons.health_and_safety, size: 80, color: AppColors.primary),
                 const SizedBox(height: 16),
                 const Text(
                   'Welcome Back',
                   textAlign: TextAlign.center,
                   style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: AppColors.textMain),
                 ),
                 const SizedBox(height: 8),
                 const Text(
                   'Sign in to continue your healing journey',
                   textAlign: TextAlign.center,
                   style: TextStyle(color: Colors.grey),
                 ),
                 const SizedBox(height: 40),
                 
                 // Email Field
                 Container(
                   decoration: BoxDecoration(
                     color: Colors.white,
                     borderRadius: BorderRadius.circular(12),
                     boxShadow: [BoxShadow(color: Colors.grey.withOpacity(0.1), blurRadius: 10)],
                   ),
                   child: TextField(
                     controller: _emailController,
                     decoration: const InputDecoration(
                       hintText: 'Email',
                       border: InputBorder.none,
                       prefixIcon: Icon(Icons.email_outlined, color: Colors.grey),
                       contentPadding: EdgeInsets.all(16),
                     ),
                   ),
                 ),
                 const SizedBox(height: 16),
                 
                 // Password Field
                 Container(
                   decoration: BoxDecoration(
                     color: Colors.white,
                     borderRadius: BorderRadius.circular(12),
                     boxShadow: [BoxShadow(color: Colors.grey.withOpacity(0.1), blurRadius: 10)],
                   ),
                   child: TextField(
                     controller: _passwordController,
                     obscureText: true,
                     decoration: const InputDecoration(
                       hintText: 'Password',
                       border: InputBorder.none,
                       prefixIcon: Icon(Icons.lock_outline, color: Colors.grey),
                       contentPadding: EdgeInsets.all(16),
                     ),
                   ),
                 ),
                 const SizedBox(height: 24),
                 
                 // Login Button
                 ElevatedButton(
                   onPressed: _isLoading ? null : _login,
                   style: ElevatedButton.styleFrom(
                     backgroundColor: AppColors.primary,
                     foregroundColor: Colors.white,
                     padding: const EdgeInsets.symmetric(vertical: 16),
                     shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                     elevation: 2,
                   ),
                   child: _isLoading 
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Text('Login', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                 ),
                 const SizedBox(height: 24),
                 
                 // Register Link
                 Row(
                   mainAxisAlignment: MainAxisAlignment.center,
                   children: [
                     const Text("Don't have an account? ", style: TextStyle(color: Colors.grey)),
                     GestureDetector(
                       onTap: () {
                         Navigator.of(context).push(MaterialPageRoute(builder: (context) => const RegisterScreen()));
                       },
                       child: const Text('Register', style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold)),
                     ),
                   ],
                 ),
               ],
             ),
           ),
         ),
       ),
     );
  }
}
