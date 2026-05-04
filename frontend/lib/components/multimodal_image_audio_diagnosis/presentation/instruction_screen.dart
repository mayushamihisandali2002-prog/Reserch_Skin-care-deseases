import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart'; // import for kIsWeb
import 'package:app/config/app_config.dart';
import 'package:app/components/multimodal_image_audio_diagnosis/data/multimodal_diagnosis_api.dart';
import 'package:app/components/multimodal_image_audio_diagnosis/presentation/result_screen.dart';
import 'package:app/services/api_service.dart';
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
  static const Map<String, List<String>> _skinConditions = {
    'Common Skin Symptoms': [
      'red',
      'redness',
      'rash',
      'itch',
      'itching',
      'itchy',
      'scratch',
      'scratching',
      'pain',
      'painful',
      'dry',
      'dryness',
      'patch',
      'patches',
      'scaly',
      'scale',
      'scales',
      'flaky',
      'cracked',
      'swelling',
      'swollen',
      'burning',
      'stinging',
      'bumps',
      'blister',
      'blisters',
      'hives',
      'welts',
      'spots',
      'sore',
      'sores',
      'oozing',
      'pus',
      'bleeding',
    ],
    'Eczema': [
      'itching',
      'dryness',
      'dry patches',
      'redness',
      'red rash',
      'cracked skin',
      'flaky skin',
      'scaly patches',
      'inflammation',
      'sensitive skin',
      'oozing',
    ],
    'Dermatitis': [
      'red rash',
      'itching',
      'swelling',
      'blisters',
      'burning',
      'irritation',
      'inflamed skin',
      'contact rash',
      'skin allergy',
      'tender rash',
    ],
    'Psoriasis': [
      'thick scales',
      'silvery scales',
      'red patches',
      'itching',
      'cracked skin',
      'bleeding skin',
      'plaque',
      'dry thick skin',
      'scaling',
      'thickened patches',
    ],
    'Acne': [
      'pimples',
      'whiteheads',
      'blackheads',
      'cystic acne',
      'nodules',
      'breakouts',
      'oily skin',
      'clogged pores',
      'pus',
      'inflamed acne',
      'acne bumps',
    ],
    'Urticaria': [
      'hives',
      'welts',
      'itching',
      'swelling',
      'raised bumps',
      'red bumps',
      'rash',
      'allergic rash',
      'skin welts',
      'burning',
    ],
    'Pigmentation / Dark Spots': [
      'dark spots',
      'uneven skin tone',
      'pigmentation',
      'hyperpigmentation',
      'sun spots',
      'brown patches',
      'dark patches',
      'discoloration',
      'darkened skin',
      'post acne marks',
    ],
    'Ringworm': [
      'ring-shaped rash',
      'circular rash',
      'round rash',
      'itching',
      'red patches',
      'scaly edges',
      'spreading rash',
      'fungal rash',
      'ring rash',
      'flaky border',
    ],
    'Rosacea': [
      'redness',
      'flushing',
      'burning',
      'stinging',
      'sensitive skin',
      'visible blood vessels',
      'facial redness',
      'cheek redness',
      'irritation',
      'warm skin',
      'red face',
    ],
    'Shingles': [
      'painful blisters',
      'burning pain',
      'one-sided rash',
      'band rash',
      'tingling',
      'stinging',
      'localized pain',
      'fluid blisters',
      'nerve pain',
      'sensitive skin',
    ],
    'Vitiligo': [
      'white patches',
      'loss of pigment',
      'depigmentation',
      'pale patches',
      'milky white skin',
      'skin color loss',
      'patchy color',
      'white spots',
      'uneven pigment',
      'lighter skin',
    ],
    'Impetigo': [
      'honey crust',
      'golden crust',
      'yellow crust',
      'oozing sores',
      'skin sores',
      'blisters',
      'scabs',
      'crusted rash',
      'red sores',
      'weeping rash',
    ],
    'Molluscum Contagiosum': [
      'pearly bumps',
      'dome bumps',
      'central dimple',
      'smooth bumps',
      'small bumps',
      'flesh-colored bumps',
      'raised papules',
      'painless bumps',
      'umbilicated bumps',
      'clustered bumps',
    ],
    'Folliculitis': [
      'hair follicle bumps',
      'red bumps',
      'pustules',
      'itching',
      'tender bumps',
      'shaving bumps',
      'inflamed follicles',
      'pus bumps',
      'hair bumps',
      'follicle pain',
    ],
    'Scabies': [
      'intense itching',
      'night itching',
      'burrows',
      'finger web itching',
      'mite rash',
      'small bumps',
      'scratch marks',
      'severe itch',
      'wrist rash',
      'household itching',
    ],
    'Warts': [
      'wart',
      'warts',
      'rough growth',
      'grainy bump',
      'cauliflower growth',
      'black dots',
      'hard bump',
      'skin growth',
      'verruca',
      'raised rough bump',
    ],
    'Seborrheic Dermatitis': [
      'dandruff',
      'greasy scales',
      'yellow scales',
      'scalp flakes',
      'flaking',
      'itchy scalp',
      'red scalp',
      'oily patches',
      'facial flaking',
      'seborrheic rash',
    ],
    'Lichen Planus': [
      'purple bumps',
      'shiny bumps',
      'flat-topped bumps',
      'itchy bumps',
      'mouth streaks',
      'white mouth lines',
      'wrist bumps',
      'ankle bumps',
      'violaceous rash',
      'skin lesions',
    ],
    'Cellulitis': [
      'hot skin',
      'swollen skin',
      'tender skin',
      'redness',
      'pain',
      'spreading redness',
      'warm swelling',
      'fever',
      'skin infection',
      'leg swelling',
    ],
    'Herpes Simplex': [
      'cold sore',
      'lip blisters',
      'fluid blisters',
      'tingling',
      'burning',
      'mouth sores',
      'painful blisters',
      'recurrent blisters',
      'crusted blisters',
      'clustered blisters',
    ],
    'Pityriasis Versicolor': [
      'light patches',
      'dark patches',
      'discolored patches',
      'chest spots',
      'back spots',
      'fine scaling',
      'tinea versicolor',
      'patchy spots',
      'itching',
      'uneven color',
    ],
    'Melanoma': [
      'asymmetrical mole',
      'irregular border',
      'multiple colors',
      'changing mole',
      'evolving lesion',
      'bleeding mole',
      'itching mole',
      'dark mole',
      'large mole',
      'new mole',
    ],
    'Basal Cell Carcinoma': [
      'pearly bump',
      'shiny bump',
      'bleeding sore',
      'non-healing sore',
      'pink lesion',
      'translucent bump',
      'visible blood vessels',
      'scabbing sore',
      'waxy bump',
      'rolled edge',
    ],
    'Actinic Keratosis': [
      'rough patch',
      'scaly patch',
      'sandpaper texture',
      'sun damaged skin',
      'pink patch',
      'crusty patch',
      'tender patch',
      'dry rough spot',
      'precancerous spot',
      'sun-exposed rash',
    ],
    'Seborrheic Keratosis': [
      'waxy growth',
      'pasted-on growth',
      'brown growth',
      'black growth',
      'crusty surface',
      'stuck-on bump',
      'rough plaque',
      'raised growth',
      'itchy growth',
      'wart-like growth',
    ],
    'Dermatofibroma': [
      'firm bump',
      'hard bump',
      'brown nodule',
      'pink nodule',
      'dimple sign',
      'leg bump',
      'small nodule',
      'tender nodule',
      'scar-like bump',
      'stable bump',
    ],
    'Cherry Angioma': [
      'red bump',
      'bright red bump',
      'cherry red spot',
      'red papule',
      'small red dot',
      'bleeding red bump',
      'blood vessel spot',
      'round red bump',
      'ruby spot',
      'vascular bump',
    ],
    'Melanocytic Nevi': [
      'mole',
      'brown mole',
      'round spot',
      'even color',
      'stable mole',
      'symmetrical spot',
      'distinct border',
      'skin-colored mole',
      'flat mole',
      'raised mole',
    ],
    'Hidradenitis Suppurativa': [
      'painful boils',
      'armpit lumps',
      'groin abscess',
      'draining tracts',
      'blackheads in pairs',
      'recurrent boils',
      'skin tunnels',
      'underarm bumps',
      'painful nodules',
      'pus drainage',
    ],
    'Alopecia Areata': [
      'round bald patches',
      'sudden hair loss',
      'patchy hair loss',
      'bald spots',
      'exclamation mark hairs',
      'nail pitting',
      'smooth bald patch',
      'hair shedding',
      'scalp patch',
      'beard hair loss',
    ],
    'Melasma': [
      'brown facial patches',
      'symmetrical discoloration',
      'forehead patches',
      'cheek hyperpigmentation',
      'worse after sun',
      'dark facial patches',
      'melasma',
      'mask-like pigmentation',
      'brown patches',
      'uneven pigment',
    ],
  };

  static const Map<String, List<String>> _expectedSymptoms = {
    'Eczema': [
      'itching',
      'dryness',
      'redness',
      'scaling',
      'cracked',
      'inflammation',
    ],
    'Dermatitis': [
      'redness',
      'itching',
      'swelling',
      'blisters',
      'rash',
      'irritation',
    ],
    'Psoriasis': [
      'scaling',
      'redness',
      'itching',
      'dryness',
      'patches',
      'thickened',
    ],
    'Acne': [
      'pimples',
      'blackheads',
      'whiteheads',
      'oily',
      'inflammation',
      'bumps',
    ],
    'Urticaria': ['swelling', 'redness', 'itching', 'bumps', 'rash', 'welts'],
    'Pigmentation / Dark Spots': [
      'spots',
      'darkened',
      'patches',
      'brown',
      'discoloration',
      'sunspot',
    ],
    'Ringworm': ['ring', 'circular', 'scaly', 'itching', 'round', 'fungal'],
    'Rosacea': [
      'redness',
      'flushing',
      'veins',
      'bumps',
      'burning',
      'sensitive',
    ],
    'Shingles': [
      'pain',
      'blisters',
      'burning',
      'band',
      'localized',
      'stinging',
    ],
    'Vitiligo': ['white', 'pigment', 'patches', 'pale', 'milky', 'color'],
    'Impetigo': ['honey', 'crust', 'scabs', 'golden', 'sores', 'yellow'],
    'Molluscum Contagiosum': ['bumps', 'pearly', 'dimple', 'smooth', 'dome'],
    'Folliculitis': ['hair', 'follicle', 'shaving', 'bumps', 'pustules', 'red'],
    'Scabies': ['itch', 'night', 'burrows', 'fingers', 'mites', 'severe'],
    'Warts': ['verruca', 'growth', 'grainy', 'rough', 'cauliflower', 'dots'],
    'Seborrheic Dermatitis': [
      'dandruff',
      'scalp',
      'flaking',
      'scale',
      'greasy',
      'yellow',
    ],
    'Lichen Planus': ['purple', 'shiny', 'flat', 'bumps', 'mouth'],
    'Cellulitis': ['hot', 'swollen', 'tender', 'redness', 'pain', 'leg'],
    'Herpes Simplex': ['cold', 'sore', 'lip', 'blisters', 'tingling', 'mouth'],
    'Pityriasis Versicolor': [
      'spots',
      'tinea',
      'patches',
      'chest',
      'discolored',
      'light',
    ],
    'Melanoma': [
      'asymmetrical mole',
      'irregular borders',
      'varying colors',
      'diameter',
      'evolving lesion',
      'itching or bleeding mole',
    ],
    'Basal Cell Carcinoma': [
      'pearly bump',
      'pink lesion',
      'sore that bleeds and heals',
      'translucent bump with blood vessels',
    ],
    'Actinic Keratosis': [
      'rough scaly patch',
      'sandpaper texture',
      'pink or red bumps',
      'sun-exposed areas',
    ],
    'Seborrheic Keratosis': [
      'waxy bump',
      'pasted-on appearance',
      'brown or black growth',
      'crusty surface',
    ],
    'Dermatofibroma': [
      'firm hard bump',
      'dimple sign when pinched',
      'pink or brown nodule',
      'found on legs',
    ],
    'Cherry Angioma': [
      'bright red bump',
      'small circular papule',
      'does not blanch with pressure',
    ],
    'Melanocytic Nevi': [
      'symmetrical round spot',
      'even brown color',
      'stable size',
      'distinct borders',
    ],
    'Hidradenitis Suppurativa': [
      'painful boils',
      'armpit lumps',
      'groin abscesses',
      'draining tracts',
      'blackheads in pairs',
    ],
    'Alopecia Areata': [
      'round bald patches',
      'sudden hair loss',
      'exclamation mark hairs',
      'nail pitting',
    ],
    'Melasma': [
      'brown facial patches',
      'symmetrical discoloration',
      'forehead cheek hyperpigmentation',
      'worse after sun',
    ],
  };

  XFile? _selectedImage;
  bool _isRecording = false;
  bool _isLoading = false;
  final TextEditingController _symptomController = TextEditingController();
  final TextEditingController _voiceTranscriptController =
      TextEditingController();

  // Speech-to-text for real-time transcription
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _speechAvailable = false;
  String _transcribedText = '';
  String _recordingBaseTranscript = '';
  String? _voiceStatusMessage;
  bool _hasTranscription = false;

  // Uploaded audio file (for backend transcription)
  Uint8List? _uploadedAudioBytes;
  String? _uploadedAudioName;
  bool _hasUploadedAudio = false;
  bool _isHistoryLoading = false;
  List<Map<String, dynamic>> _scanHistory = [];

  @override
  void initState() {
    super.initState();
    _initSpeech();
    _loadScanHistory();
  }

  Future<void> _initSpeech() async {
    try {
      _speechAvailable = await _speech.initialize(
        onError: (error) {
          debugPrint('Speech error: $error');
          if (mounted) {
            setState(() {
              _isRecording = false;
              _voiceStatusMessage =
                  'Voice recognition error: ${error.errorMsg}. Try again or use Upload.';
            });
          }
        },
        onStatus: (status) {
          debugPrint('Speech status: $status');
          if (mounted && (status == 'done' || status == 'notListening')) {
            setState(() => _isRecording = false);
          }
        },
      );
    } catch (e) {
      _speechAvailable = false;
    }
    setState(() {});
  }

  Future<void> _loadScanHistory() async {
    setState(() => _isHistoryLoading = true);
    try {
      final history = await ApiService.getScanHistory(limit: 30);
      if (!mounted) return;
      setState(() {
        _scanHistory = history
            .whereType<Map>()
            .map((item) => Map<String, dynamic>.from(item))
            .toList();
      });
    } catch (_) {
      if (mounted) setState(() => _scanHistory = []);
    } finally {
      if (mounted) setState(() => _isHistoryLoading = false);
    }
  }

  @override
  void dispose() {
    _speech.stop();
    _symptomController.dispose();
    _voiceTranscriptController.dispose();
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
      setState(() => _selectedImage = pickedFile);
    }
  }

  void _toggleRecording() async {
    if (!_isRecording) {
      bool hasPermission = await _requestMicrophonePermission();
      if (!hasPermission) {
        setState(() {
          _voiceStatusMessage = 'Microphone permission is required.';
        });
        return;
      }
    }

    if (_isRecording) {
      await _speech.stop();
      setState(() {
        _isRecording = false;
        _hasTranscription = _transcribedText.isNotEmpty;
      });
    } else {
      if (!_speechAvailable) {
        setState(() {
          _voiceStatusMessage =
              'Speech recognition is not available in this browser. Try Chrome microphone permissions or use Upload.';
        });
        return;
      }
      setState(() {
        _isRecording = true;
        _recordingBaseTranscript = _transcribedText.trim();
        _voiceStatusMessage = null;
        _hasTranscription = false;
      });

      final options = stt.SpeechListenOptions(partialResults: true);
      await _speech.listen(
        onResult: (result) {
          setState(() {
            final currentWords = result.recognizedWords.trim();
            _transcribedText = _recordingBaseTranscript.isEmpty
                ? currentWords
                : currentWords.isEmpty
                ? _recordingBaseTranscript
                : '$_recordingBaseTranscript\n\n$currentWords';
            _voiceTranscriptController.value = TextEditingValue(
              text: _transcribedText,
              selection: TextSelection.collapsed(
                offset: _transcribedText.length,
              ),
            );
            _hasTranscription = _transcribedText.trim().isNotEmpty;
          });
        },
        listenFor: const Duration(minutes: 2),
        pauseFor: const Duration(seconds: 8),
        localeId: 'en_US',
        listenOptions: options,
      );
    }
  }

  void _deleteTranscription() {
    setState(() {
      _transcribedText = '';
      _recordingBaseTranscript = '';
      _voiceStatusMessage = null;
      _hasTranscription = false;
      _symptomController.clear();
      _voiceTranscriptController.clear();
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
        withData: true,
      );
      if (result != null) {
        final file = result.files.first;
        final audioBytes =
            file.bytes ??
            (!kIsWeb && file.path != null
                ? await File(file.path!).readAsBytes()
                : null);
        if (audioBytes == null) return;
        setState(() {
          _uploadedAudioBytes = audioBytes;
          _uploadedAudioName = file.name;
          _voiceTranscriptController.clear();
          _transcribedText = '';
          _voiceStatusMessage =
              'Uploaded ${file.name}. The backend will transcribe and check minimum keywords when you run the scan.';
          _hasUploadedAudio = true;
          _hasTranscription = false;
        });
      }
    } catch (_) {}
  }

  bool get _isSymptomValid {
    return _keywordCount(_effectiveSymptomText()) >= 4 || _hasUploadedAudio;
  }

  String _effectiveSymptomText() {
    final typedText = _symptomController.text.trim();
    final voiceText = _voiceTranscriptController.text.trim();
    if (typedText.isEmpty) return voiceText;
    if (voiceText.isEmpty) return typedText;
    return '$typedText\n\n$voiceText';
  }

  String _normalizeKeywordText(String text) {
    final buffer = StringBuffer();
    for (final codeUnit in text.toLowerCase().codeUnits) {
      final isNumber = codeUnit >= 48 && codeUnit <= 57;
      final isLetter = codeUnit >= 97 && codeUnit <= 122;
      buffer.write(isNumber || isLetter ? String.fromCharCode(codeUnit) : ' ');
    }
    return buffer
        .toString()
        .split(RegExp(r'\s+'))
        .where((item) => item.isNotEmpty)
        .join(' ');
  }

  Set<String> _keywordVariants(String normalizedKeyword) {
    final variants = <String>{normalizedKeyword};
    final words = normalizedKeyword.split(' ');
    if (words.isEmpty) return variants;

    final lastWord = words.last;
    if (lastWord.endsWith('ies') && lastWord.length > 4) {
      variants.add(
        [
          ...words.take(words.length - 1),
          '${lastWord.substring(0, lastWord.length - 3)}y',
        ].join(' '),
      );
    } else if (_needsEsSingular(lastWord)) {
      variants.add(
        [
          ...words.take(words.length - 1),
          lastWord.substring(0, lastWord.length - 2),
        ].join(' '),
      );
    } else if (lastWord.endsWith('s') && lastWord.length > 3) {
      variants.add(
        [
          ...words.take(words.length - 1),
          lastWord.substring(0, lastWord.length - 1),
        ].join(' '),
      );
    } else if (lastWord.length > 2) {
      variants.add([...words.take(words.length - 1), '${lastWord}s'].join(' '));
    }
    return variants;
  }

  bool _needsEsSingular(String word) {
    return word.length > 4 &&
        (word.endsWith('ches') ||
            word.endsWith('shes') ||
            word.endsWith('xes') ||
            word.endsWith('zes') ||
            word.endsWith('ses'));
  }

  Map<String, List<String>> get _validationKeywordCategories => {
    'Common Skin Symptoms': _skinConditions['Common Skin Symptoms'] ?? const [],
    ..._expectedSymptoms,
  };

  int _keywordCount(String text) {
    final normalizedText = ' ${_normalizeKeywordText(text)} ';
    final matches = <String>{};
    final seenVariants = <String>{};
    for (final keywords in _validationKeywordCategories.values) {
      for (final keyword in keywords) {
        final normalizedKeyword = _normalizeKeywordText(keyword);
        if (normalizedKeyword.isEmpty) continue;
        final variants = _keywordVariants(normalizedKeyword);
        final matched = variants.any(
          (variant) => normalizedText.contains(' $variant '),
        );
        if (matched && seenVariants.intersection(variants).isEmpty) {
          seenVariants.addAll(variants);
          matches.add(normalizedKeyword);
        }
      }
    }
    return matches.length;
  }

  Widget _buildKeywordValidationInfo() {
    final text = _effectiveSymptomText();
    if (text.trim().isEmpty && !_hasUploadedAudio) {
      return const SizedBox.shrink();
    }
    if (text.trim().isEmpty && _hasUploadedAudio) {
      return const Padding(
        padding: EdgeInsets.only(top: 8, left: 4),
        child: Row(
          children: [
            Icon(Icons.info_outline, size: 15, color: AppColors.primary),
            SizedBox(width: 6),
            Text(
              'Minimum keywords are four. Uploaded audio will be checked after transcription.',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: AppColors.primary,
              ),
            ),
          ],
        ),
      );
    }
    final count = _keywordCount(text);
    final valid = count >= 4;
    return Padding(
      padding: const EdgeInsets.only(top: 8, left: 4),
      child: Row(
        children: [
          Icon(
            valid ? Icons.check_circle_outline : Icons.info_outline,
            size: 15,
            color: valid ? AppColors.success : AppColors.error,
          ),
          const SizedBox(width: 6),
          Text(
            valid
                ? 'Minimum keywords met ($count/4, mismatch symptoms allowed)'
                : 'Minimum keywords are four ($count/4, any symptom class)',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: valid ? AppColors.success : AppColors.error,
            ),
          ),
        ],
      ),
    );
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
        journeyId: null,
      );
      final status = result['status']?.toString();
      if (status == 'validation_error' ||
          status == 'requires_symptom_context') {
        final message =
            result['message']?.toString() ??
            result['error_message']?.toString() ??
            'Minimum keywords are four.';
        if (mounted) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text(message)));
        }
        return;
      }
      if (mounted) {
        await Navigator.of(context).push(
          MaterialPageRoute(builder: (context) => ResultScreen(data: result)),
        );
        if (mounted) {
          await _loadScanHistory();
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final Color voiceStateColor = _hasUploadedAudio || _hasTranscription
        ? AppColors.success
        : _isRecording
        ? AppColors.error
        : AppColors.secondary;
    final bool canAnalyze =
        !_isLoading && _selectedImage != null && _isSymptomValid;

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
              const SizedBox(height: 16),
              _buildImageSection(),
              const SizedBox(height: 16),
              _buildSymptomsSection(voiceStateColor),
              const SizedBox(height: 18),
              _buildAnalyzeButton(canAnalyze),
              const SizedBox(height: 18),
              _buildScanHistorySection(),
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
              const Icon(
                Icons.auto_fix_high_rounded,
                color: Colors.white,
                size: 20,
              ),
              const SizedBox(width: 12),
              const Text(
                'SYSTEM SCAN PREPARATION',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w900,
                  color: Colors.white70,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Text(
            'Take a Clear Photo',
            style: TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.w900,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 10),
          const Text(
            'For accuracy, ensure good lighting and focus.',
            style: TextStyle(fontSize: 14, color: Colors.white70),
          ),
        ],
      ),
    );
  }

  Widget _buildTipsCard() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: AppDecor.softCard(
        context,
        color: context.clrSurface.withValues(alpha: 0.88),
      ),
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
        Text(
          label,
          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
        ),
      ],
    );
  }

  Widget _buildMedicalInfoBanner() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.warning.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(18),
      ),
      child: const Row(
        children: [
          Icon(
            Icons.medical_information_outlined,
            color: AppColors.warning,
            size: 22,
          ),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'System scan needs both an image and your symptoms for a safe analysis.',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
            ),
          ),
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
          const Text(
            'Scan Your Skin',
            style: TextStyle(fontWeight: FontWeight.w900, fontSize: 22),
          ),
          const SizedBox(height: 14),
          GestureDetector(
            onTap: () => _pickImage(ImageSource.gallery),
            child: Container(
              height: 200,
              width: double.infinity,
              decoration: BoxDecoration(
                color: context.clrSurface,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: context.clrBorder),
              ),
              child: _selectedImage == null
                  ? const Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.add_a_photo_rounded, size: 32),
                        Text('Tap to select image'),
                      ],
                    )
                  : ClipRRect(
                      borderRadius: BorderRadius.circular(23),
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
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: () => _pickImage(ImageSource.camera),
                  icon: const Icon(Icons.photo_camera),
                  label: const Text('Camera'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _pickImage(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library),
                  label: const Text('Gallery'),
                ),
              ),
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
          const Text(
            'Symptom Context',
            style: TextStyle(fontWeight: FontWeight.w900, fontSize: 20),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _symptomController,
            maxLines: 3,
            onChanged: (val) => setState(() {}),
            decoration: InputDecoration(
              hintText: _isRecording
                  ? 'Listening... your voice transcript will appear here'
                  : 'Describe itch, pain, duration, or use voice...',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
              ),
            ),
          ),
          _buildKeywordValidationInfo(),
          const SizedBox(height: 12),
          LayoutBuilder(
            builder: (context, constraints) {
              final controls = _buildVoiceControls(voiceColor);
              final transcriptBox = _buildVoiceTranscriptBox();
              if (constraints.maxWidth < 720) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    controls,
                    const SizedBox(height: 12),
                    transcriptBox,
                  ],
                );
              }
              return Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  controls,
                  const SizedBox(width: 12),
                  Expanded(child: transcriptBox),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildVoiceControls(Color voiceColor) {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: [
        _voiceButton(
          icon: _isRecording ? Icons.stop : Icons.mic,
          label: _isRecording ? 'Stop' : 'Voice',
          color: voiceColor,
          onTap: _toggleRecording,
        ),
        _voiceButton(
          icon: Icons.upload_file,
          label: 'Upload',
          color: AppColors.primary,
          onTap: _pickAudioFile,
        ),
        if (_hasTranscription || _hasUploadedAudio)
          _voiceButton(
            icon: Icons.delete,
            label: 'Clear',
            color: AppColors.error,
            onTap: _deleteTranscription,
          ),
      ],
    );
  }

  Widget _buildVoiceTranscriptBox() {
    return ConstrainedBox(
      constraints: const BoxConstraints(minHeight: 120),
      child: TextField(
        minLines: 4,
        maxLines: 6,
        controller: _voiceTranscriptController,
        keyboardType: TextInputType.multiline,
        textInputAction: TextInputAction.newline,
        onChanged: (value) {
          setState(() {
            _transcribedText = value;
            _hasTranscription = value.trim().isNotEmpty;
          });
        },
        decoration: InputDecoration(
          labelText: 'Voice to Text Transcript',
          helperText:
              _voiceStatusMessage ??
              (_isRecording
                  ? 'Listening now. Keep speaking and the text will appear here.'
                  : 'Press Voice and start talking. All recognized words appear here.'),
          helperMaxLines: 2,
          hintText: _isRecording
              ? 'Listening...'
              : 'Your voice-to-text words will show in this box.',
          prefixIcon: Icon(
            _isRecording ? Icons.graphic_eq : Icons.record_voice_over_outlined,
            color: _isRecording ? AppColors.error : AppColors.secondary,
          ),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
    );
  }

  Widget _voiceButton({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.15),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.4)),
        ),
        child: Row(
          children: [
            Icon(icon, size: 18, color: color),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(color: color, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }

  String? _resolveImageUrl(String? value) {
    final raw = value?.trim();
    if (raw == null || raw.isEmpty || raw.startsWith('uploaded_via_')) {
      return null;
    }
    if (raw.startsWith('http://') || raw.startsWith('https://')) return raw;
    if (raw.startsWith('/')) return '${AppConfig.apiBaseUrl}$raw';
    return raw;
  }

  String _formatHistoryDate(dynamic value) {
    final parsed = DateTime.tryParse(value?.toString() ?? '');
    if (parsed == null) return 'Saved scan';
    final local = parsed.toLocal();
    final month = local.month.toString().padLeft(2, '0');
    final day = local.day.toString().padLeft(2, '0');
    final hour = local.hour.toString().padLeft(2, '0');
    final minute = local.minute.toString().padLeft(2, '0');
    return '${local.year}-$month-$day $hour:$minute';
  }

  void _openHistoryResult(Map<String, dynamic> item) {
    final response = item['response'];
    final resultData = response is Map
        ? Map<String, dynamic>.from(response)
        : _historyFallbackResult(item);
    final imageUrl = item['image_url']?.toString();
    if (imageUrl != null && imageUrl.trim().isNotEmpty) {
      resultData['image_url'] ??= imageUrl;
      final diagnosis = resultData['diagnosis'];
      if (diagnosis is Map) {
        diagnosis['image_url'] ??= imageUrl;
      }
    }
    Navigator.of(context).push(
      MaterialPageRoute(builder: (context) => ResultScreen(data: resultData)),
    );
  }

  Map<String, dynamic> _historyFallbackResult(Map<String, dynamic> item) {
    final disease = (item['predicted_disease'] ?? 'Unknown').toString();
    final transcript = (item['transcript'] ?? '').toString().trim();
    final confidence = item['confidence'] is num
        ? (item['confidence'] as num).toDouble()
        : double.tryParse(item['confidence']?.toString() ?? '') ?? 0.0;
    return {
      'image_url': item['image_url'],
      'summary':
          'Saved prediction history for $disease. Symptom context: ${transcript.isEmpty ? 'not recorded' : transcript}.',
      'diagnosis': {
        'disease': disease,
        'display_disease': disease,
        'final_diagnosis': disease,
        'confidence': confidence,
        'confidence_level': item['confidence_level'] ?? 'low',
        'mismatch_detected': item['mismatch_detected'] == true,
        'transcript': transcript,
        'image_url': item['image_url'],
        'model_used': item['model_used'] ?? 'history_record',
        'treatments': const [],
        'recommended_treatments': const [],
        'medical_disclaimer': 'This is not a medical diagnosis',
      },
    };
  }

  Widget _buildScanHistorySection() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: AppDecor.softCard(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Prediction History',
                  style: TextStyle(fontWeight: FontWeight.w900, fontSize: 20),
                ),
              ),
              IconButton(
                tooltip: 'Refresh',
                onPressed: _isHistoryLoading ? null : _loadScanHistory,
                icon: _isHistoryLoading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.refresh),
              ),
            ],
          ),
          const SizedBox(height: 8),
          if (_scanHistory.isEmpty)
            Text(
              _isHistoryLoading
                  ? 'Loading saved predictions...'
                  : 'No saved scan predictions yet.',
              style: TextStyle(color: context.clrTextSec),
            )
          else
            Column(children: _scanHistory.map(_buildHistoryTile).toList()),
        ],
      ),
    );
  }

  Widget _buildHistoryTile(Map<String, dynamic> item) {
    final imageUrl = _resolveImageUrl(item['image_url']?.toString());
    final hasSavedImage = imageUrl != null;
    final disease = (item['predicted_disease'] ?? 'Unknown').toString();
    final transcript = (item['transcript'] ?? '').toString().trim();
    final symptomPreview = transcript.isEmpty
        ? 'No symptom context saved'
        : transcript;
    final confidence = item['confidence'] is num
        ? (item['confidence'] as num).toDouble()
        : double.tryParse(item['confidence']?.toString() ?? '') ?? 0;
    final mismatch = item['mismatch_detected'] == true;
    return InkWell(
      onTap: () => _openHistoryResult(item),
      borderRadius: BorderRadius.circular(14),
      child: Container(
        margin: const EdgeInsets.only(top: 10),
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          border: Border.all(color: context.clrBorder),
          borderRadius: BorderRadius.circular(14),
          color: context.clrSurface,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: SizedBox(
                    width: 82,
                    height: 62,
                    child: imageUrl == null
                        ? Container(
                            color: context.clrBorder.withValues(alpha: 0.35),
                            child: const Icon(
                              Icons.image_not_supported_outlined,
                            ),
                          )
                        : Image.network(imageUrl, fit: BoxFit.cover),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        disease,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontWeight: FontWeight.w800,
                          fontSize: 14,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${_formatHistoryDate(item['created_at'])} - ${(confidence * 100).toStringAsFixed(1)}% confidence',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 12,
                          color: context.clrTextSec,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        hasSavedImage
                            ? 'Skin image saved'
                            : 'Skin image not available',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: hasSavedImage
                              ? AppColors.success
                              : context.clrTextSec,
                        ),
                      ),
                    ],
                  ),
                ),
                if (mismatch)
                  const Padding(
                    padding: EdgeInsets.only(right: 8),
                    child: Icon(
                      Icons.warning_amber_rounded,
                      color: AppColors.error,
                    ),
                  ),
                const Icon(Icons.chevron_right),
              ],
            ),
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: context.clrSurface.withValues(alpha: 0.72),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: context.clrBorder.withValues(alpha: 0.7),
                ),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.notes_rounded,
                    size: 16,
                    color: AppColors.primary,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Symptom context: $symptomPreview',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 12,
                        color: context.clrTextMain,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
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
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
        child: _isLoading
            ? const CircularProgressIndicator(color: Colors.white)
            : const Text(
                'Run Clinical Scan',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
      ),
    );
  }
}
