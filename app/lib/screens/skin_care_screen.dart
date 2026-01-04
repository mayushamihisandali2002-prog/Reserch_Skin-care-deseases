import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import '../services/api_service.dart';
import '../utils/app_styles.dart';

class SkinCareScreen extends StatefulWidget {
  const SkinCareScreen({super.key});

  @override
  State<SkinCareScreen> createState() => _SkinCareScreenState();
}

class _SkinCareScreenState extends State<SkinCareScreen> {
  XFile? _selectedImage;
  bool _isLoading = false;
  Map<String, dynamic>? _analysisResult;

  Future<void> _pickImage(ImageSource source) async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: source);

    if (pickedFile != null) {
      setState(() {
        _selectedImage = pickedFile;
        _analysisResult = null; // Reset result on new image
      });
    }
  }

  Future<void> _analyzeSkin() async {
    if (_selectedImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please upload an image first.')),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final result = await ApiService.analyzeSkinCare(_selectedImage!.path);
      
      if (!mounted) return;
      
      setState(() {
        _analysisResult = result;
      });
      
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Skin Care Assistant')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: _analysisResult == null ? _buildInputView() : _buildResultView(),
      ),
    );
  }

  Widget _buildInputView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text(
          'Upload a clear selfie for personalized skin care advice.',
          style: AppTextStyles.subHeading,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 20),
        
        // Image Area
        GestureDetector(
          onTap: () => _pickImage(ImageSource.gallery),
          child: Container(
            height: 300,
            decoration: BoxDecoration(
              color: Colors.grey[200],
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.green[200]!, width: 2),
            ),
            child: _selectedImage == null
                ? Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Icon(Icons.face_retouching_natural, size: 60, color: Colors.green),
                      SizedBox(height: 8),
                      Text('Tap to select photo'),
                    ],
                  )
                : ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: kIsWeb
                        ? Image.network(_selectedImage!.path, fit: BoxFit.cover)
                        : Image.file(File(_selectedImage!.path), fit: BoxFit.cover),
                  ),
          ),
        ),
        const SizedBox(height: 20),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            ElevatedButton.icon(
              onPressed: () => _pickImage(ImageSource.camera),
              icon: const Icon(Icons.camera_alt),
              label: const Text('Camera'),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
            ),
            ElevatedButton.icon(
              onPressed: () => _pickImage(ImageSource.gallery),
              icon: const Icon(Icons.photo_library),
              label: const Text('Gallery'),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
            ),
          ],
        ),

        const SizedBox(height: 40),

        // Analyze Button
        SizedBox(
          height: 50,
          child: ElevatedButton(
            onPressed: _isLoading ? null : _analyzeSkin,
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green[700],
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: _isLoading 
                ? const CircularProgressIndicator(color: Colors.white)
                : const Text('Analyze Skin', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ),
        ),
      ],
    );
  }

  Widget _buildResultView() {
    final String skinType = _analysisResult!['skin_type'] ?? 'Unknown';
    final String skinColor = _analysisResult!['skin_color'] ?? 'Unknown';
    final List recommendations = _analysisResult!['recommendations'] ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.green[50], // Light green background
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.green[200]!),
          ),
          child: Row(
            children: [
               const Icon(Icons.check_circle, color: Colors.green, size: 40),
               const SizedBox(width: 16),
               Expanded(
                 child: Column(
                   crossAxisAlignment: CrossAxisAlignment.start,
                   children: [
                     const Text('Skin Type', style: TextStyle(color: Colors.grey)),
                     Text(skinType, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.green)),
                     const SizedBox(height: 8),
                     const Text('Skin Tone', style: TextStyle(color: Colors.grey)),
                     Text(skinColor, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
                   ],
                 ),
               )
            ],
          ),
        ),
        const SizedBox(height: 24),
        
        const Text('Natural Treatments & Advice', style: AppTextStyles.subHeading),
        const SizedBox(height: 12),
        
        ...recommendations.map((rec) => Padding(
          padding: const EdgeInsets.only(bottom: 12.0),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.eco, color: Colors.green),
              const SizedBox(width: 12),
              Expanded(child: Text(rec.toString(), style: const TextStyle(fontSize: 16))),
            ],
          ),
        )).toList(),
        
        const SizedBox(height: 30),
        SizedBox(
          width: double.infinity,
          height: 50,
          child: OutlinedButton(
            onPressed: () {
              setState(() {
                _selectedImage = null;
                _analysisResult = null;
              });
            },
            child: const Text('Analyze Another Photo'),
          ),
        )
      ],
    );
  }
}
