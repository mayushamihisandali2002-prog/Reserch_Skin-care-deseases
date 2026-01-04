import 'package:flutter/material.dart';
import '../utils/app_styles.dart';
import 'home_container.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;

  void _register() async {
    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 1)); // Mock register
    if (mounted) {
       setState(() => _isLoading = false);
       // Navigate to HomeContainer
       Navigator.of(context).pushAndRemoveUntil(
         MaterialPageRoute(builder: (context) => const HomeContainer()),
         (route) => false,
       );
    }
  }

  @override
  Widget build(BuildContext context) {
     return Scaffold(
       appBar: AppBar(backgroundColor: Colors.transparent, elevation: 0, iconTheme: const IconThemeData(color: Colors.black)),
       extendBodyBehindAppBar: true,
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
                 const Text(
                   'Create Account',
                   textAlign: TextAlign.center,
                   style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: AppColors.textMain),
                 ),
                 const SizedBox(height: 8),
                 const Text(
                   'Join us to track and improve your skin health',
                   textAlign: TextAlign.center,
                   style: TextStyle(color: Colors.grey),
                 ),
                 const SizedBox(height: 40),
                 
                  // Name Field
                 Container(
                   decoration: BoxDecoration(
                     color: Colors.white,
                     borderRadius: BorderRadius.circular(12),
                     boxShadow: [BoxShadow(color: Colors.grey.withOpacity(0.1), blurRadius: 10)],
                   ),
                   child: TextField(
                     controller: _nameController,
                     decoration: const InputDecoration(
                       hintText: 'Full Name',
                       border: InputBorder.none,
                       prefixIcon: Icon(Icons.person_outline, color: Colors.grey),
                       contentPadding: EdgeInsets.all(16),
                     ),
                   ),
                 ),
                 const SizedBox(height: 16),

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
                 
                 // Register Button
                 ElevatedButton(
                   onPressed: _isLoading ? null : _register,
                   style: ElevatedButton.styleFrom(
                     backgroundColor: AppColors.primary,
                     foregroundColor: Colors.white,
                     padding: const EdgeInsets.symmetric(vertical: 16),
                     shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                     elevation: 2,
                   ),
                   child: _isLoading 
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Text('Sign Up', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                 ),
                 const SizedBox(height: 24),

                 // Login Link
                 Row(
                   mainAxisAlignment: MainAxisAlignment.center,
                   children: [
                     const Text("Already have an account? ", style: TextStyle(color: Colors.grey)),
                     GestureDetector(
                       onTap: () {
                         Navigator.of(context).pop();
                       },
                       child: const Text('Login', style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold)),
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
