# 🩺 Skin Care Assistant

AI-powered skin disease diagnosis and treatment recommendation system using deep learning.

## 📋 Features

- **AI-Powered Diagnosis**: Uses fine-tuned DistilBERT (text) and ResNet-18 (image) models
- **Multi-Modal Analysis**: Combine text symptoms and skin images for accurate diagnosis
- **Treatment Recommendations**: Evidence-based treatment suggestions from a curated knowledge base
- **Real-time Chat**: Interactive symptom checker with conversation memory
- **Progress Tracking**: Monitor skin condition improvement over time
- **User Authentication**: Secure accounts via Supabase Auth
- **Cloud Database**: Persistent storage with Supabase PostgreSQL

## 🏗️ Project Structure

```
Reserch_Skin-care-deseases/
├── app/                          # Flutter mobile/web app
│   ├── lib/
│   │   ├── config/               # App & Supabase configuration
│   │   ├── screens/              # UI screens
│   │   ├── services/             # API & database services
│   │   └── utils/                # Shared utilities
│   └── pubspec.yaml              # Flutter dependencies
│
├── backend/                      # Flask API server
│   ├── app.py                    # Main Flask application
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # Environment configuration
│   ├── assets/
│   │   ├── models/               # AI models
│   │   │   ├── distilbert/       # Text classification model
│   │   │   ├── image_best_finetuned.pt  # Image classification model
│   │   │   └── *.pkl             # Legacy sklearn models
│   │   └── data/                 # Knowledge base CSVs
│   ├── database/                 # Database schema
│   │   └── schema.sql            # PostgreSQL tables
│   ├── inference/                # AI inference modules
│   │   ├── config.py             # Model paths & settings
│   │   ├── distilbert_model.py   # DistilBERT text classifier
│   │   ├── image_model.py        # ResNet-18 image classifier
│   │   └── inference.py          # Unified inference pipeline
│   └── services/                 # Backend services
│       └── supabase_service.py   # Database operations
│
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Flutter 3.0+
- Supabase account (free tier works)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env with your Supabase credentials

# Start server
python app.py
```

The API will be available at `http://127.0.0.1:5000`

### 2. Flutter App Setup

```bash
cd app

# Install dependencies
flutter pub get

# Run on Chrome (recommended for development)
flutter run -d chrome

# Or run on Android
flutter run -d android
```

### 3. Database Setup (Supabase)

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Go to SQL Editor → Run `backend/database/schema.sql`
4. Create storage bucket named `skin-images`
5. Update credentials in:
   - `app/lib/config/supabase_config.dart`
   - `backend/.env`

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/status` | Model availability |
| POST | `/api/chat` | Text-based diagnosis |
| POST | `/api/analyze` | Image-based diagnosis |
| POST | `/api/analyze-fused` | Combined image + text |
| GET | `/api/history` | Progress history |
| GET | `/api/stats` | Symptom statistics |

### Example: Chat API

```bash
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I have red itchy patches on my arms", "session_id": "123"}'
```

## 🧠 AI Models

### DistilBERT Text Classifier
- **Architecture**: DistilBERT base (66M params)
- **Training**: Fine-tuned on skin disease symptoms
- **Classes**: Eczema, Dermatitis, Psoriasis, Acne, Urticaria
- **Location**: `backend/assets/models/distilbert/`

### ResNet-18 Image Classifier
- **Architecture**: ResNet-18 (11M params)
- **Training**: Fine-tuned on skin condition images
- **Classes**: Same 5 diseases
- **Location**: `backend/assets/models/image_best_finetuned.pt`

### Fusion Strategy
When both text and image are provided:
```
P_final = 0.6 × P_image + 0.4 × P_text
```

## 📱 App Screens

- **Login/Register**: User authentication
- **Dashboard**: Overview and quick stats
- **Chat**: Interactive symptom checker
- **Analyze**: Upload images for diagnosis
- **Progress**: Track healing over time

## 🔐 Environment Variables

### Backend (.env)
```env
FLASK_ENV=development
FLASK_DEBUG=true
HOST=0.0.0.0
PORT=5000
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
LOG_LEVEL=DEBUG
```

### Flutter (supabase_config.dart)
```dart
static const String supabaseUrl = 'https://xxx.supabase.co';
static const String supabaseAnonKey = 'your_anon_key';
```

## 🧪 Testing

```bash
# Test inference pipeline
cd backend
python -c "from inference import get_inference_pipeline; p = get_inference_pipeline(); print(p.predict_disease('red itchy skin'))"

# Test API
curl http://127.0.0.1:5000/api/status
```

## 📦 Production Deployment

### Backend (e.g., Railway, Render)
1. Set environment variables in hosting platform
2. Use `gunicorn app:app` for production WSGI

### Flutter Web (e.g., Firebase Hosting)
```bash
flutter build web
# Deploy build/web folder
```

## ⚠️ Disclaimer

This application provides AI-based suggestions only and is **NOT** a substitute for professional medical diagnosis. Always consult a qualified dermatologist for proper medical advice.

## 📄 License

MIT License - See LICENSE file for details.