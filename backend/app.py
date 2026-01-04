from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

# Dummy Data
MOCK_HISTORY = [
    {"week": "Week 1", "date": "2025-11-01", "image_url": "assets/images/week1.png", "status": "Bad", "score": 30, "metrics": {"redness": 90, "inflammation": 85, "scaling": 70, "texture": 60}},
    {"week": "Week 2", "date": "2025-11-08", "image_url": "assets/images/week2.png", "status": "Poor", "score": 45, "metrics": {"redness": 80, "inflammation": 75, "scaling": 65, "texture": 65}},
    {"week": "Week 3", "date": "2025-11-15", "image_url": "assets/images/week3.png", "status": "Improving", "score": 60, "metrics": {"redness": 60, "inflammation": 55, "scaling": 50, "texture": 70}},
    {"week": "Week 4", "date": "2025-11-22", "image_url": "assets/images/week4.png", "status": "Better", "score": 75, "metrics": {"redness": 40, "inflammation": 35, "scaling": 30, "texture": 80}},
    {"week": "Week 5", "date": "2025-11-29", "image_url": "assets/images/week5.png", "status": "Good", "score": 85, "metrics": {"redness": 20, "inflammation": 15, "scaling": 10, "texture": 90}},
    {"week": "Week 6", "date": "2025-12-06", "image_url": "assets/images/week6.png", "status": "Excellent", "score": 95, "metrics": {"redness": 5, "inflammation": 5, "scaling": 0, "texture": 95}},
]

MOCK_STATS = {
    "labels": ["Redness", "Itch", "Dryness", "Scaling"],
    "values": [20, 40, 25, 15] # Dummy distribution of current symptoms
}

@app.route('/api/analyze', methods=['POST'])
def analyze():
    # Simulate analysis delay if needed
    return jsonify({
        "prediction": "Eczema",
        "confidence": 0.85,
        "symptoms": ["Redness", "Itching", "Dryness"],
        "triggers": ["Stress", "Dry Air", "Soap"],
        "routine": {
            "morning": "Gentle Cleanser, Moisturizer",
            "night": "Topical Corticosteroid (if prescribed), Heavy Cream",
            "treatment": "Use prescribed ointment twice daily"
        },
        "warnings": ["If bleeding occurs, see a doctor immediately."]
    })

@app.route('/api/analyze-skin-care', methods=['POST'])
def analyze_skin_care():
    return jsonify({
        "skin_type": "Combination",
        "skin_color": "Fair - Medium",
        "recommendations": [
            "Use a gentle foaming cleanser.",
            "Apply a lightweight, oil-free moisturizer.",
            "Use sunscreen with SPF 30+ daily.",
            "Exfoliate 1-2 times a week with a mild chemical exfoliant."
        ]
    })

@app.route('/api/history', methods=['GET'])
def history():
    return jsonify(MOCK_HISTORY)

@app.route('/api/stats', methods=['GET'])
def stats():
    return jsonify(MOCK_STATS)

@app.route('/api/progress', methods=['POST'])
def add_progress():
    # In a real app, handle image upload here
    new_score = 90 + len(MOCK_HISTORY) # Dummy logic to increase score
    new_entry = {
        "week": f"Week {len(MOCK_HISTORY) + 1}",
        "date": datetime.date.today().isoformat(),
        "image_url": "assets/images/placeholder.png",
        "status": "Improving",
        "score": 85 + (len(MOCK_HISTORY) % 15),
        "metrics": {
            "redness": 10,
            "inflammation": 10,
            "scaling": 5,
            "texture": 92
        }
    }
    MOCK_HISTORY.append(new_entry)
    
    return jsonify({
        "message": "Progress logged successfully",
        "analysis": "Based on the new image, inflammation has reduced by 15% compared to last week.",
        "new_entry": new_entry
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    # Simple dummy response logic
    response_text = "I'm a dummy AI. I recommend seeing a dermatologist for accurate advice."
    if "itch" in user_message.lower():
        response_text = "Itching can be relieved with cold compresses and moisturizers."
    elif "sun" in user_message.lower():
        response_text = "Always wear sunscreen to protect sensitive skin."
        
    return jsonify({"response": response_text})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
