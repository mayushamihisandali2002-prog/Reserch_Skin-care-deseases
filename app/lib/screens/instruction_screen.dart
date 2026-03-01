import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart'; // import for kIsWeb
import 'dart:typed_data';
import 'package:image_picker/image_picker.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:permission_handler/permission_handler.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:io';
import '../services/api_service.dart';
import '../utils/app_styles.dart';
import 'result_screen.dart';

class InstructionScreen extends StatefulWidget {
  const InstructionScreen({super.key});

  @override
  State<InstructionScreen> createState() => _InstructionScreenState();
}

class _InstructionScreenState extends State<InstructionScreen> {
  XFile? _selectedImage;
  bool _isRecording = false;
  bool _isLoading = false;

  // Speech-to-text for real-time transcription
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _speechAvailable = false;
  String _transcribedText = '';
  bool _hasTranscription = false;

  // Uploaded audio file (for backend transcription)
  Uint8List? _uploadedAudioBytes;
  String? _uploadedAudioName;
  bool _hasUploadedAudio = false;

  @override
  void initState() {
    super.initState();
    _initSpeech();
  }

  Future<void> _initSpeech() async {
    try {
      _speechAvailable = await _speech.initialize(
        onError: (error) {
          debugPrint('Speech error: $error');
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Speech error: ${error.errorMsg}')),
            );
          }
        },
        onStatus: (status) => debugPrint('Speech status: $status'),
      );
      debugPrint('Speech recognition available: $_speechAvailable');
      if (!_speechAvailable && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Speech recognition not supported on this browser. Use Upload instead.',
            ),
            duration: Duration(seconds: 5),
          ),
        );
      }
    } catch (e) {
      debugPrint('Speech init error: $e');
      _speechAvailable = false;
    }
    setState(() {});
  }

  @override
  void dispose() {
    _speech.stop();
    super.dispose();
  }

  Future<bool> _requestMicrophonePermission() async {
    if (kIsWeb) return true;

    var status = await Permission.microphone.status;
    if (status.isDenied) {
      status = await Permission.microphone.request();
    }
    return status.isGranted;
  }

  Future<void> _pickImage(ImageSource source) async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: source);

    if (pickedFile != null) {
      setState(() {
        _selectedImage = pickedFile;
      });
    }
  }

  void _toggleRecording() async {
    // Check microphone permission
    if (!_isRecording) {
      bool hasPermission = await _requestMicrophonePermission();
      if (!hasPermission) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Microphone permission required')),
          );
        }
        return;
      }
    }

    if (_isRecording) {
      // Stop listening
      await _speech.stop();
      setState(() {
        _isRecording = false;
        _hasTranscription = _transcribedText.isNotEmpty;
      });
      if (mounted && _hasTranscription) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Voice transcription complete!')),
        );
      }
    } else {
      // Start listening
      if (!_speechAvailable) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Speech recognition not available')),
          );
        }
        return;
      }

      setState(() {
        _isRecording = true;
        _transcribedText = '';
        _hasTranscription = false;
      });

      await _speech.listen(
        onResult: (result) {
          setState(() {
            _transcribedText = result.recognizedWords;
            if (result.finalResult) {
              _hasTranscription = _transcribedText.isNotEmpty;
            }
          });
        },
        listenFor: const Duration(seconds: 30),
        pauseFor: const Duration(seconds: 3),
        partialResults: true,
        localeId: 'en_US',
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Listening... Speak your symptoms')),
        );
      }
    }
  }

  void _deleteTranscription() {
    setState(() {
      _transcribedText = '';
      _hasTranscription = false;
      _uploadedAudioBytes = null;
      _uploadedAudioName = null;
      _hasUploadedAudio = false;
    });
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Voice input cleared')));
  }

  Future<void> _pickAudioFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['wav', 'wave', 'mp3', 'm4a', 'aac', 'ogg', 'webm'],
        allowMultiple: false,
      );

      if (result != null && result.files.isNotEmpty) {
        final file = result.files.first;
        final fileName = file.name.toLowerCase();

        // Check if it's a WAV file (best compatibility)
        final isWav = fileName.endsWith('.wav') || fileName.endsWith('.wave');
        if (!isWav) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text(
                    'WAV files are recommended. If transcription fails, convert the voice note to WAV and try again.',
                  ),
                  duration: Duration(seconds: 3),
                ),
            );
          }
        }

        if (kIsWeb) {
          // On web, use bytes directly
          if (file.bytes != null) {
            setState(() {
              _uploadedAudioBytes = file.bytes;
              _uploadedAudioName = file.name;
              _transcribedText = ''; // Clear live transcription
              _hasTranscription = false;
              _hasUploadedAudio = true;
            });
          }
        } else {
          // On mobile/desktop, read from path
          if (file.path != null) {
            final audioFile = File(file.path!);
            final bytes = await audioFile.readAsBytes();
            setState(() {
              _uploadedAudioBytes = bytes;
              _uploadedAudioName = file.name;
              _transcribedText = ''; // Clear live transcription
              _hasTranscription = false;
              _hasUploadedAudio = true;
            });
          }
        }

        if (mounted && _hasUploadedAudio) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(
                'Voice note uploaded! Will be transcribed on server.',
              ),
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error picking audio file: $e')));
      }
    }
  }

  Future<void> _analyze() async {
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
      // Read image as bytes (works on all platforms including web)
      final imageBytes = await _selectedImage!.readAsBytes();
      final imageFileName = _selectedImage!.name;

      final Map<String, dynamic> result;

      if (_hasUploadedAudio && _uploadedAudioBytes != null) {
        // Multimodal fusion: Image + Audio (send audio for server-side transcription)
        result = await ApiService.analyzeFusedWithAudio(
          imageBytes,
          imageFileName,
          _uploadedAudioBytes!,
          _uploadedAudioName ?? 'audio.wav',
        );
      } else if (_hasTranscription && _transcribedText.isNotEmpty) {
        // Multimodal fusion: Image + Text (transcribed speech)
        result = await ApiService.analyzeFused(
          imageBytes,
          imageFileName,
          _transcribedText, // Send transcribed text directly
        );
      } else {
        // Image-only analysis
        result = await ApiService.analyzeSkin(imageBytes, imageFileName);
      }

      if (!mounted) return;

      Navigator.of(context).push(
        MaterialPageRoute(builder: (context) => ResultScreen(data: result)),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: $e')));
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
      appBar: AppBar(title: const Text('New Scan')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Upload a clear photo of the affected area.',
              style: AppTextStyles.subHeading,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),

            // Image Area
            GestureDetector(
              onTap: () => _pickImage(ImageSource.gallery),
              child: Container(
                height: 250,
                decoration: BoxDecoration(
                  color: Colors.grey[200],
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.grey[300]!),
                ),
                child: _selectedImage == null
                    ? Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          Icon(Icons.add_a_photo, size: 50, color: Colors.grey),
                          SizedBox(height: 8),
                          Text('Tap to select image'),
                        ],
                      )
                    : ClipRRect(
                        borderRadius: BorderRadius.circular(16),
                        child: kIsWeb
                            ? Image.network(
                                _selectedImage!.path,
                                fit: BoxFit.cover,
                              )
                            : Image.file(
                                File(_selectedImage!.path),
                                fit: BoxFit.cover,
                              ),
                      ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: () => _pickImage(ImageSource.camera),
                  icon: const Icon(Icons.camera),
                  label: const Text('Camera'),
                ),
                ElevatedButton.icon(
                  onPressed: () => _pickImage(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library),
                  label: const Text('Gallery'),
                ),
              ],
            ),

            const SizedBox(height: 40),

            // Voice Symptom Description Section
            const Text(
              'Describe your symptoms (Optional)',
              style: AppTextStyles.subHeading,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            const Text(
              'Tap the mic and speak to describe your symptoms',
              style: TextStyle(color: Colors.grey, fontSize: 12),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),

            // Voice Recording Section
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: (_hasTranscription || _hasUploadedAudio)
                    ? Colors.green.withOpacity(0.1)
                    : _isRecording
                    ? Colors.red.withOpacity(0.1)
                    : Colors.grey.withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: (_hasTranscription || _hasUploadedAudio)
                      ? Colors.green.withOpacity(0.3)
                      : _isRecording
                      ? Colors.red.withOpacity(0.3)
                      : Colors.grey.withOpacity(0.2),
                ),
              ),
              child: Column(
                children: [
                  Text(
                    _hasUploadedAudio
                        ? 'Voice note uploaded: $_uploadedAudioName'
                        : _hasTranscription
                        ? 'Symptoms captured'
                        : _isRecording
                        ? 'Listening...'
                        : 'Tap the mic to speak or upload a voice note',
                    style: TextStyle(
                      color: (_hasTranscription || _hasUploadedAudio)
                          ? Colors.green
                          : _isRecording
                          ? Colors.red
                          : Colors.grey,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Live transcript display or uploaded audio info
                  if (_transcribedText.isNotEmpty ||
                      _isRecording ||
                      _hasUploadedAudio)
                    Container(
                      padding: const EdgeInsets.all(12),
                      margin: const EdgeInsets.only(bottom: 12),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.grey.withOpacity(0.2)),
                      ),
                      width: double.infinity,
                      child: Text(
                        _hasUploadedAudio
                            ? 'Audio file: $_uploadedAudioName\n(Will be transcribed on server)'
                            : _transcribedText.isEmpty
                            ? 'Speak now...'
                            : _transcribedText,
                        style: TextStyle(
                          color:
                              (_hasUploadedAudio || _transcribedText.isNotEmpty)
                              ? Colors.black87
                              : Colors.grey,
                          fontSize: 14,
                          fontStyle:
                              (_hasUploadedAudio || _transcribedText.isNotEmpty)
                              ? FontStyle.normal
                              : FontStyle.italic,
                        ),
                      ),
                    ),

                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Record Button
                      Column(
                        children: [
                          GestureDetector(
                            onTap: _toggleRecording,
                            child: Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: _isRecording
                                    ? Colors.red
                                    : _hasTranscription
                                    ? Colors.green
                                    : AppColors.secondary.withOpacity(0.8),
                                boxShadow: [
                                  BoxShadow(
                                    color:
                                        (_isRecording
                                                ? Colors.red
                                                : AppColors.secondary)
                                            .withOpacity(0.3),
                                    blurRadius: 10,
                                    spreadRadius: 2,
                                  ),
                                ],
                              ),
                              child: Icon(
                                _isRecording
                                    ? Icons.stop
                                    : _hasTranscription
                                    ? Icons.check
                                    : Icons.mic,
                                color: Colors.white,
                                size: 28,
                              ),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _isRecording ? 'Stop' : 'Speak',
                            style: TextStyle(
                              color: _isRecording ? Colors.red : Colors.grey,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(width: 24),
                      // Upload Button
                      Column(
                        children: [
                          GestureDetector(
                            onTap: _pickAudioFile,
                            child: Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: _hasUploadedAudio
                                    ? Colors.green
                                    : Colors.blue.withOpacity(0.8),
                                boxShadow: [
                                  BoxShadow(
                                    color:
                                        (_hasUploadedAudio
                                                ? Colors.green
                                                : Colors.blue)
                                            .withOpacity(0.3),
                                    blurRadius: 10,
                                    spreadRadius: 2,
                                  ),
                                ],
                              ),
                              child: Icon(
                                _hasUploadedAudio
                                    ? Icons.check
                                    : Icons.upload_file,
                                color: Colors.white,
                                size: 28,
                              ),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Upload',
                            style: TextStyle(
                              color: _hasUploadedAudio
                                  ? Colors.green
                                  : Colors.grey,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                      if (_hasTranscription || _hasUploadedAudio) ...[
                        const SizedBox(width: 24),
                        // Clear Button
                        Column(
                          children: [
                            GestureDetector(
                              onTap: _deleteTranscription,
                              child: Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: Colors.red.withOpacity(0.1),
                                  border: Border.all(
                                    color: Colors.red.withOpacity(0.3),
                                  ),
                                ),
                                child: const Icon(
                                  Icons.delete_outline,
                                  color: Colors.red,
                                  size: 24,
                                ),
                              ),
                            ),
                            const SizedBox(height: 4),
                            const Text(
                              'Clear',
                              style: TextStyle(color: Colors.red, fontSize: 11),
                            ),
                          ],
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (!_speechAvailable)
                    const Text(
                      'Speech recognition unavailable. Upload audio file instead.',
                      style: TextStyle(color: Colors.orange, fontSize: 11),
                      textAlign: TextAlign.center,
                    ),
                ],
              ),
            ),

            const SizedBox(height: 30),

            // Analyze Button
            SizedBox(
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _analyze,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text(
                        'Send & Analyze',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
