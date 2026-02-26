# Skin Care Disease Research Application - Setup Summary

## Project Overview

This is a **Skin Care Disease Analysis Application** built with:

- **Frontend**: Flutter (Mobile & Web)
- **Backend**: Python Flask API

### Application Features

- 🩺 Skin disease analysis with ML predictions (e.g., Eczema detection)
- 📊 Progress tracking with historical data visualization
- 💊 Treatment recommendations and symptom analysis
- 👤 User authentication (login/register)
- 💬 Chat functionality for consultation
- 📈 Analytics dashboard with skin metrics

---

## Setup Status ✅

### 1. **Environment Preparation**

- ✅ Flutter 3.38.5 installed and configured
- ✅ Dart 3.10.4 available
- ✅ Python 3.13.1 installed
- ✅ Android SDK configured (Android development ready)
- ✅ Chrome browser available (web testing)

### 2. **Frontend Setup (Flutter App)**

- ✅ Project location: `app/`
- ✅ Flutter dependencies installed via `flutter pub get`
- ✅ Key dependencies:
  - `http: ^1.2.0` - API communication
  - `google_fonts: ^6.1.0` - Typography
  - `fl_chart: ^0.66.0` - Data visualization
  - `image_picker: ^1.1.2` - Image selection
  - `flutter_svg: ^2.0.10` - SVG support
  - `intl: ^0.19.0` - Internationalization

### 3. **Backend Setup (Flask API)**

- ✅ Project location: `backend/`
- ✅ Python dependencies installed:
  - `Flask 3.1.0` - Web framework
  - `flask-cors 6.0.2` - Cross-origin support
- ✅ API Server running on:
  - **Host**: 0.0.0.0 (all interfaces)
  - **Port**: 5000
  - **URL**: http://localhost:5000
  - **Debug Mode**: Enabled (development)

### 4. **Running Services**

#### Backend Server (Flask) - RUNNING ✅

```
Port: 5000
Status: Active (debug mode)
Available Endpoints:
- POST /api/analyze - Skin disease analysis
- POST /api/analyze-skin-care - Skin care recommendations
```

#### Frontend App (Flutter) - STARTING ✅

```
Platform: Chrome (Web)
Status: Launching in debug mode
Port: Typically localhost:PORT (auto-assigned)
```

---

## API Endpoints

### POST `/api/analyze`

Analyzes skin condition and provides diagnosis
**Response Example:**

```json
{
  "prediction": "Eczema",
  "confidence": 0.85,
  "symptoms": ["Redness", "Itching", "Dryness"],
  "triggers": ["Stress", "Dry Air", "Soap"],
  "routine": {
    "morning": "Gentle Cleanser, Moisturizer",
    "night": "Topical Corticosteroid (if prescribed), Heavy Cream"
  },
  "warnings": ["If bleeding occurs, see a doctor immediately."]
}
```

### POST `/api/analyze-skin-care`

Provides personalized skin care recommendations
**Response Example:**

```json
{
  "skin_type": "Combination",
  "skin_color": "Fair - Medium",
  "recommendations": [
    "Use a gentle foaming cleanser.",
    "Apply a lightweight, oil-free moisturizer.",
    "Use sunscreen with SPF 30+ daily."
  ]
}
```

---

## Project Structure

```
Reserch_Skin-care-deseases/
├── app/                          # Flutter Frontend
│   ├── lib/
│   │   ├── main.dart            # App entry point
│   │   ├── screens/             # UI screens
│   │   │   ├── login_screen.dart
│   │   │   ├── dashboard_screen.dart
│   │   │   ├── analyze_screen.dart
│   │   │   ├── progress_screen.dart
│   │   │   └── ...
│   │   ├── services/
│   │   │   └── api_service.dart # API communication
│   │   └── utils/
│   │       └── app_styles.dart  # Theme & colors
│   ├── pubspec.yaml             # Flutter dependencies
│   ├── android/                 # Android configuration
│   ├── ios/                     # iOS configuration
│   ├── web/                     # Web configuration
│   └── windows/                 # Windows desktop app
│
├── backend/                     # Python Flask Backend
│   ├── app.py                   # Flask app & API routes
│   └── requirements.txt          # Python dependencies
│
└── README.md
```

---

## Available Platforms to Run

1. **Web (Chrome)** ✅ - Currently launching
2. **Web (Edge)** - Available
3. **Windows Desktop** - Available
4. **Android** - Available (requires Android emulator/device)
5. **iOS** - Available (requires macOS)

---

## Commands Reference

### Frontend Commands

```bash
# Get dependencies
flutter pub get

# Run on specific platform
flutter run -d chrome          # Web (Chrome)
flutter run -d windows         # Windows desktop
flutter run -d android         # Android device/emulator

# Build for production
flutter build web              # Build web app
flutter build windows          # Build Windows app
flutter build apk              # Build Android APK
```

### Backend Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask server
python app.py

# Run with custom host/port
python -c "from app import app; app.run(host='0.0.0.0', port=5000, debug=True)"
```

---

## Next Steps

1. ✅ Backend API is running and ready for requests
2. ⏳ Frontend app is loading in Chrome
3. Once fully loaded, you can:
   - Test user authentication (Login/Register screens)
   - Upload skin images for analysis
   - View historical progress data
   - Get personalized skin care recommendations
   - Test API endpoints with the Flutter UI

---

## Notes

- The app uses CORS for cross-origin requests, allowing web frontend to communicate with the Flask backend
- Mock data is currently used in the API endpoints for demonstration
- Development server is running in debug mode - not suitable for production
- Some optional Windows-specific development tools (Visual Studio) are not installed but not required for running the app

---

## Troubleshooting

### If Flutter app doesn't appear in Chrome:

1. Wait 30-60 seconds for compilation to complete
2. Check Chrome for popup browser window
3. Run: `flutter run -d chrome -v` for verbose output

### If backend API is not accessible:

1. Verify Flask is running: Check terminal for "Running on http://127.0.0.1:5000"
2. Test with: `curl http://localhost:5000/api/analyze -X POST`
3. Ensure port 5000 is not blocked by firewall

### If you get Dart SDK version error:

- The Flutter upgrade has already resolved this (upgraded to 3.38.5)

---

**Project Setup Completed**: January 4, 2026
