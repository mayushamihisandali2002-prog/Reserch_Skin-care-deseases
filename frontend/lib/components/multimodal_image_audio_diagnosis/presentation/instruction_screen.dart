import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart'; // import for kIsWeb
import 'package:app/components/multimodal_image_audio_diagnosis/data/multimodal_diagnosis_api.dart';
import 'package:app/components/multimodal_image_audio_diagnosis/presentation/result_screen.dart';
import 'package:app/services/supabase_service.dart';
import 'package:app/utils/app_styles.dart';
import 'package:image_picker/image_picker.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:permission_handler/permission_handler.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:io';

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
  List<Map<String, dynamic>> _journeys = [];
  String? _selectedJourneyId;

  @override
  void initState() {
    super.initState();
    _loadJourneys();
    _initSpeech();
  }

  Future<void> _loadJourneys() async {
    try {
      final journeys = await SupabaseService.getJourneys();
      setState(() {
        _journeys = journeys;
        if (_journeys.isNotEmpty) {
          // No auto-selection by default to keep it optional
        }
      });
    } catch (_) {}
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

      final options = stt.SpeechListenOptions(partialResults: true);
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
        localeId: 'en_US',
        listenOptions: options,
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
        result = await MultimodalDiagnosisApi.analyzeFusedWithAudio(
          imageBytes,
          imageFileName,
          _uploadedAudioBytes!,
          _uploadedAudioName ?? 'audio.wav',
          journeyId: _selectedJourneyId,
        );
      } else if (_hasTranscription && _transcribedText.isNotEmpty) {
        // Multimodal fusion: Image + Text (transcribed speech)
        result = await MultimodalDiagnosisApi.analyzeFused(
          imageBytes,
          imageFileName,
          _transcribedText, // Send transcribed text directly
          journeyId: _selectedJourneyId,
        );
      } else {
        // Image-only analysis
        result = await MultimodalDiagnosisApi.analyzeImage(
          imageBytes,
          imageFileName,
          journeyId: _selectedJourneyId,
        );
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
    final Color voiceStateColor = _hasUploadedAudio || _hasTranscription
        ? AppColors.success
        : _isRecording
        ? AppColors.error
        : AppColors.secondary;

    return Scaffold(
      appBar: AppBar(title: const Text('New Skin Scan')),
      body: Container(
        decoration: BoxDecoration(gradient: AppGradients.page(context)),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  gradient: AppGradients.premium,
                  borderRadius: BorderRadius.circular(28),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.3),
                      blurRadius: 20,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(
                            Icons.auto_fix_high_rounded,
                            color: Colors.white,
                            size: 20,
                          ),
                        ),
                        const SizedBox(width: 12),
                        const Text(
                          'AI SCAN PREPARATION',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 1.5,
                            color: Colors.white70,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Capture High-Quality Input',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w900,
                        color: Colors.white,
                        height: 1.1,
                      ),
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'For the most accurate diagnosis, ensure focus and natural lighting.',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.white70,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: AppDecor.softCard(
                  context,
                  color: context.clrSurface.withValues(alpha: 0.88),
                  borderColor: context.clrBorder.withValues(alpha: 0.9),
                ),
                child: Row(
                  children: [
                    _tip(icon: Icons.wb_sunny_outlined, label: 'Good lighting'),
                    const SizedBox(width: 10),
                    _tip(
                      icon: Icons.face_retouching_natural,
                      label: 'No filters',
                    ),
                    const SizedBox(width: 10),
                    _tip(
                      icon: Icons.center_focus_strong,
                      label: 'Focused view',
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.warning.withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(
                    color: AppColors.warning.withValues(alpha: 0.30),
                  ),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(
                      Icons.medical_information_outlined,
                      color: AppColors.warning,
                      size: 22,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        '⚠️ Warning: Image-only scanning cannot reliably detect critical conditions like Melanoma. You must add voice symptoms for a safe fused diagnostic review.',
                        style: TextStyle(
                          fontSize: 13,
                          height: 1.45,
                          color: context.clrTextMain,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              if (_journeys.isNotEmpty) ...[
                const SizedBox(height: 16),
                _buildJourneySelector(),
              ],
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: AppDecor.softCard(context),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Face Image',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Upload one clear selfie or skin-area photo.',
                      style: AppTextStyles.body(context),
                    ),
                    const SizedBox(height: 14),
                    GestureDetector(
                      onTap: () => _pickImage(ImageSource.gallery),
                      child: Container(
                        height: 280,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: context.clrSurface,
                          borderRadius: BorderRadius.circular(24),
                          border: Border.all(
                            color: context.clrBorder.withValues(alpha: 0.5),
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withValues(alpha: 0.03),
                              blurRadius: 15,
                              offset: const Offset(0, 5),
                            ),
                          ],
                        ),
                        child: _selectedImage == null
                            ? Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Container(
                                    width: 80,
                                    height: 80,
                                    decoration: BoxDecoration(
                                      color: AppColors.primary.withValues(
                                        alpha: 0.05,
                                      ),
                                      shape: BoxShape.circle,
                                    ),
                                    child: Icon(
                                      Icons.add_a_photo_rounded,
                                      size: 32,
                                      color: AppColors.primary,
                                    ),
                                  ),
                                  const SizedBox(height: 16),
                                  Text(
                                    'Select Diagnostic Image',
                                    style: AppTextStyles.bodyStrong(context),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Tap to browse gallery',
                                    style: AppTextStyles.caption(context),
                                  ),
                                ],
                              )
                            : ClipRRect(
                                borderRadius: BorderRadius.circular(23),
                                child: Stack(
                                  children: [
                                    Positioned.fill(
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
                                    Positioned(
                                      right: 12,
                                      top: 12,
                                      child: Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 10,
                                          vertical: 6,
                                        ),
                                        decoration: BoxDecoration(
                                          color: Colors.black45,
                                          borderRadius: BorderRadius.circular(
                                            10,
                                          ),
                                        ),
                                        child: const Text(
                                          'SELECTED',
                                          style: TextStyle(
                                            color: Colors.white,
                                            fontSize: 10,
                                            fontWeight: FontWeight.w900,
                                          ),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                      ),
                    ),
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        Expanded(
                          child: FilledButton.icon(
                            onPressed: () => _pickImage(ImageSource.camera),
                            icon: const Icon(Icons.photo_camera_outlined),
                            label: const Text('Camera'),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () => _pickImage(ImageSource.gallery),
                            icon: const Icon(Icons.photo_library_outlined),
                            label: const Text('Gallery'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: AppDecor.softCard(context),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: voiceStateColor.withValues(alpha: 0.14),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Icon(
                            _hasUploadedAudio
                                ? Icons.upload_file
                                : _isRecording
                                ? Icons.mic
                                : Icons.keyboard_voice_outlined,
                            size: 20,
                            color: voiceStateColor,
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'Voice Symptoms (Optional)',
                            style: AppTextStyles.subHeading(context),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _voiceStateText(),
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: voiceStateColor,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: context.clrSurface,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: context.clrBorder.withValues(alpha: 0.5)),
                      ),
                      child: Text(
                        _voiceDetailText(),
                        style: TextStyle(
                          fontSize: 13,
                          color:
                              _hasUploadedAudio || _transcribedText.isNotEmpty
                              ? context.clrTextMain
                              : context.clrTextSec,
                          fontStyle:
                              _hasUploadedAudio || _transcribedText.isNotEmpty
                              ? FontStyle.normal
                              : FontStyle.italic,
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: [
                        _voiceActionButton(
                          icon: _isRecording
                              ? Icons.stop_circle_outlined
                              : _hasTranscription
                              ? Icons.check_circle_outline
                              : Icons.mic_none_rounded,
                          label: _isRecording
                              ? 'Stop Recording'
                              : 'Record Voice',
                          onTap: _toggleRecording,
                          color: _isRecording
                              ? AppColors.error
                              : _hasTranscription
                              ? AppColors.success
                              : AppColors.secondary,
                        ),
                        _voiceActionButton(
                          icon: _hasUploadedAudio
                              ? Icons.check_circle_outline
                              : Icons.upload_file_outlined,
                          label: _hasUploadedAudio
                              ? 'Audio Uploaded'
                              : 'Upload Audio',
                          onTap: _pickAudioFile,
                          color: _hasUploadedAudio
                              ? AppColors.success
                              : AppColors.primary,
                        ),
                        if (_hasTranscription || _hasUploadedAudio)
                          _voiceActionButton(
                            icon: Icons.delete_outline,
                            label: 'Clear',
                            onTap: _deleteTranscription,
                            color: AppColors.error,
                          ),
                      ],
                    ),
                    if (!_speechAvailable) ...[
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppColors.warning.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(
                            color: AppColors.warning.withValues(alpha: 0.4),
                          ),
                        ),
                        child: const Row(
                          children: [
                            Icon(
                              Icons.info_outline,
                              size: 16,
                              color: AppColors.warning,
                            ),
                            SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'Speech recognition not available on this device. Use Upload Audio.',
                                style: TextStyle(
                                  color: AppColors.warning,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 18),
              SizedBox(
                height: 54,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: _isLoading
                        ? LinearGradient(
                            colors: [
                              context.clrTextSec.withValues(alpha: 0.6),
                              context.clrTextSec.withValues(alpha: 0.5),
                            ],
                          )
                        : const LinearGradient(
                            colors: [AppColors.primary, AppColors.primaryDark],
                          ),
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: _isLoading
                        ? null
                        : [
                            BoxShadow(
                              color: AppColors.primary.withValues(alpha: 0.28),
                              blurRadius: 14,
                              offset: const Offset(0, 6),
                            ),
                          ],
                  ),
                  child: ElevatedButton.icon(
                    onPressed: _isLoading ? null : _analyze,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.transparent,
                      shadowColor: Colors.transparent,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                    icon: _isLoading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.4,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(
                            Icons.analytics_outlined,
                            color: Colors.white,
                          ),
                    label: Text(
                      _isLoading ? 'Analyzing...' : 'Analyze Skin Condition',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                        fontSize: 16,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildJourneySelector() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: AppDecor.softCard(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Tracking Journey (Optional)',
            style: AppTextStyles.bodyStrong(context),
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            initialValue: _selectedJourneyId,
            hint: const Text('Continue a tracking journey...'),
            isExpanded: true,
            decoration: const InputDecoration(
              border: InputBorder.none,
              prefixIcon: Icon(
                Icons.track_changes_rounded,
                color: AppColors.primary,
              ),
            ),
            items: _journeys.map((j) {
              return DropdownMenuItem(
                value: j['id'].toString(),
                child: Text(j['title'] ?? 'Untitled Journey'),
              );
            }).toList(),
            onChanged: (val) => setState(() => _selectedJourneyId = val),
          ),
        ],
      ),
    );
  }

  Widget _tip({required IconData icon, required String label}) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.75),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: context.clrBorder.withValues(alpha: 0.8)),
        ),
        child: Row(
          children: [
            Icon(icon, size: 16, color: AppColors.primaryDark),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: context.clrTextMain,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _voiceActionButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    required Color color,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.35)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 18, color: color),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.w700,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _voiceStateText() {
    if (_hasUploadedAudio) {
      return 'Audio uploaded: ${_uploadedAudioName ?? "voice note"}';
    }
    if (_hasTranscription) {
      return 'Voice transcription captured';
    }
    if (_isRecording) {
      return 'Listening... speak your symptoms';
    }
    return 'Record directly or upload a voice note for symptom context';
  }

  String _voiceDetailText() {
    if (_hasUploadedAudio) {
      return 'Audio file: ${_uploadedAudioName ?? "voice note"}\n'
          '(transcription happens on the backend)';
    }
    if (_transcribedText.isNotEmpty) {
      return _transcribedText;
    }
    if (_isRecording) {
      return 'Listening for up to 30 seconds...';
    }
    return 'No voice content added yet.';
  }
}
