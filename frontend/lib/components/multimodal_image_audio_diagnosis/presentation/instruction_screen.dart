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
  final TextEditingController _symptomController = TextEditingController();

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
      });
    } catch (_) {}
  }

  Future<void> _initSpeech() async {
    try {
      _speechAvailable = await _speech.initialize(
        onError: (error) {
          debugPrint('Speech error: $error');
        },
        onStatus: (status) => debugPrint('Speech status: $status'),
      );
    } catch (e) {
      _speechAvailable = false;
    }
    setState(() {});
  }

  @override
  void dispose() {
    _speech.stop();
    _symptomController.dispose();
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
    if (!_isRecording) {
      bool hasPermission = await _requestMicrophonePermission();
      if (!hasPermission) return;
    }

    if (_isRecording) {
      await _speech.stop();
      setState(() {
        _isRecording = false;
        _hasTranscription = _transcribedText.isNotEmpty;
      });
    } else {
      if (!_speechAvailable) return;
      setState(() {
        _isRecording = true;
        _transcribedText = '';
        _hasTranscription = false;
      });

      await _speech.listen(
        onResult: (result) {
          setState(() {
            _transcribedText = result.recognizedWords;
            _hasTranscription = _transcribedText.isNotEmpty;
          });
        },
        localeId: 'en_US',
      );
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
  }

  Future<void> _pickAudioFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['wav', 'mp3', 'm4a'],
      );
      if (result != null) {
        final file = result.files.first;
        setState(() {
          _uploadedAudioBytes = file.bytes;
          _uploadedAudioName = file.name;
          _hasUploadedAudio = true;
        });
      }
    } catch (_) {}
  }

  bool get _hasSymptomContext => 
    _symptomController.text.trim().isNotEmpty || 
    _transcribedText.isNotEmpty || 
    _hasUploadedAudio;

  String _effectiveSymptomText() {
    String text = _symptomController.text.trim();
    if (_transcribedText.isNotEmpty) {
      text = text.isEmpty ? _transcribedText : '$text\n\nVoice Transcript: $_transcribedText';
    }
    return text;
  }

  Future<void> _analyze() async {
    setState(() => _isLoading = true);
    try {
      final imageBytes = await _selectedImage!.readAsBytes();
      final result = await MultimodalDiagnosisApi.analyzeFused(
        imageBytes,
        _selectedImage!.name,
        _effectiveSymptomText(),
        audioBytes: _uploadedAudioBytes,
        audioFileName: _uploadedAudioName,
        journeyId: _selectedJourneyId,
      );
      if (mounted) {
        Navigator.of(context).push(
          MaterialPageRoute(builder: (context) => ResultScreen(data: result)),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final Color voiceStateColor = _hasUploadedAudio || _hasTranscription 
        ? AppColors.success 
        : _isRecording ? AppColors.error : AppColors.secondary;
    final bool canAnalyze = !_isLoading && _selectedImage != null && _hasSymptomContext;

    return Scaffold(
      appBar: AppBar(title: const Text('New Skin Scan')),
      body: Container(
        decoration: BoxDecoration(gradient: AppGradients.page(context)),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildModernHero(),
              const SizedBox(height: 14),
              _buildTipsCard(),
              const SizedBox(height: 14),
              _buildMedicalInfoBanner(),
              if (_journeys.isNotEmpty) ...[
                const SizedBox(height: 16),
                _buildJourneySelector(),
              ],
              const SizedBox(height: 16),
              _buildImageSection(),
              const SizedBox(height: 16),
              _buildSymptomsSection(voiceStateColor),
              const SizedBox(height: 18),
              _buildAnalyzeButton(canAnalyze),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildModernHero() {
    return Container(
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
              const Icon(Icons.auto_fix_high_rounded, color: Colors.white, size: 20),
              const SizedBox(width: 12),
              const Text('AI SCAN PREPARATION', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w900, color: Colors.white70)),
            ],
          ),
          const SizedBox(height: 16),
          const Text('Take a Clear Photo', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900, color: Colors.white)),
          const SizedBox(height: 10),
          const Text('For accuracy, ensure good lighting and focus.', style: TextStyle(fontSize: 14, color: Colors.white70)),
        ],
      ),
    );
  }

  Widget _buildTipsCard() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: AppDecor.softCard(context, color: context.clrSurface.withValues(alpha: 0.88)),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _tip(icon: Icons.wb_sunny_outlined, label: 'Lighting'),
          _tip(icon: Icons.face_retouching_natural, label: 'No filters'),
          _tip(icon: Icons.center_focus_strong, label: 'Focus'),
        ],
      ),
    );
  }

  Widget _tip({required IconData icon, required String label}) {
    return Column(
      children: [
        Icon(icon, color: AppColors.primary, size: 20),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
      ],
    );
  }

  Widget _buildMedicalInfoBanner() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: AppColors.warning.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(18)),
      child: Row(
        children: [
          const Icon(Icons.medical_information_outlined, color: AppColors.warning, size: 22),
          const SizedBox(width: 10),
          const Expanded(child: Text('AI needs both an image and your symptoms for a safe diagnosis.', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600))),
        ],
      ),
    );
  }

  Widget _buildImageSection() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: AppDecor.softCard(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Scan Your Skin', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 22)),
          const SizedBox(height: 14),
          GestureDetector(
            onTap: () => _pickImage(ImageSource.gallery),
            child: Container(
              height: 200,
              width: double.infinity,
              decoration: BoxDecoration(color: context.clrSurface, borderRadius: BorderRadius.circular(24), border: Border.all(color: context.clrBorder)),
              child: _selectedImage == null
                  ? const Column(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.add_a_photo_rounded, size: 32), Text('Tap to select image')])
                  : ClipRRect(
                      borderRadius: BorderRadius.circular(23), 
                      child: kIsWeb 
                        ? Image.network(_selectedImage!.path, fit: BoxFit.cover)
                        : Image.file(File(_selectedImage!.path), fit: BoxFit.cover),
                    ),
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(child: FilledButton.icon(onPressed: () => _pickImage(ImageSource.camera), icon: const Icon(Icons.photo_camera), label: const Text('Camera'))),
              const SizedBox(width: 10),
              Expanded(child: OutlinedButton.icon(onPressed: () => _pickImage(ImageSource.gallery), icon: const Icon(Icons.photo_library), label: const Text('Gallery'))),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSymptomsSection(Color voiceColor) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: AppDecor.softCard(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Symptom Context', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 20)),
          const SizedBox(height: 10),
          TextField(
            controller: _symptomController,
            maxLines: 3,
            decoration: InputDecoration(hintText: 'Describe itch, pain, duration...', border: OutlineInputBorder(borderRadius: BorderRadius.circular(16))),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _voiceButton(icon: _isRecording ? Icons.stop : Icons.mic, label: _isRecording ? 'Stop' : 'Voice', color: voiceColor, onTap: _toggleRecording),
              const SizedBox(width: 10),
              _voiceButton(icon: Icons.upload_file, label: 'Upload', color: AppColors.primary, onTap: _pickAudioFile),
              if (_hasTranscription || _hasUploadedAudio) ...[
                const SizedBox(width: 10),
                _voiceButton(icon: Icons.delete, label: 'Clear', color: AppColors.error, onTap: _deleteTranscription),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _voiceButton({required IconData icon, required String label, required Color color, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(color: color.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(12), border: Border.all(color: color.withValues(alpha: 0.4))),
        child: Row(children: [Icon(icon, size: 18, color: color), const SizedBox(width: 6), Text(label, style: TextStyle(color: color, fontWeight: FontWeight.bold))]),
      ),
    );
  }

  Widget _buildAnalyzeButton(bool canAnalyze) {
    return SizedBox(
      height: 56,
      child: ElevatedButton(
        onPressed: canAnalyze ? _analyze : null,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        child: _isLoading ? const CircularProgressIndicator(color: Colors.white) : const Text('Run Clinical Scan', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
      ),
    );
  }

  Widget _buildJourneySelector() {
    return DropdownButtonFormField<String>(
      decoration: const InputDecoration(labelText: 'Tracking Journey (Optional)', border: OutlineInputBorder()),
      items: _journeys.map((j) => DropdownMenuItem(value: j['id'].toString(), child: Text(j['title']))).toList(),
      onChanged: (val) => setState(() => _selectedJourneyId = val),
    );
  }
}
