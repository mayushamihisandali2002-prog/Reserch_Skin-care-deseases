"""
Intent Classifier for routing messages
Classifies user input into: symptom_description, ask_treatment, ask_about_disease, 
                           ask_severity, ask_advice, ask_causes, other
"""

import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

class IntentClassifier:
    """Lightweight intent classifier using TF-IDF + Naive Bayes"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=150, lowercase=True)
        self.classifier = MultinomialNB()
        self.intent_map = {
            0: 'symptom_description',
            1: 'ask_treatment',
            2: 'ask_about_disease',
            3: 'ask_severity',
            4: 'ask_advice',
            5: 'ask_causes',
            6: 'ask_healing',
            7: 'ask_worsening',
            8: 'general_question',
            9: 'other'
        }
        self.trained = False
        self._train()
    
    def _train(self):
        """Train on synthetic intent dataset"""
        
        # Synthetic training data - expanded for better coverage
        training_texts = [
            # Symptom descriptions (0)
            'i have red itchy skin', 'my skin is dry and flaky',
            'i have pimples on my face', 'severe itching on my hands',
            'skin is inflamed and red', 'large scaly patches',
            'oily skin with breakouts', 'burning sensation on skin',
            'rash on my arms', 'itchy hives all over',
            'its on my arms very itchy and red', 'i have bumps on my face',
            'my skin is peeling', 'i noticed some spots on my legs',
            'there are blisters forming', 'my scalp is flaking',
            
            # Ask treatment (1)
            'what is the treatment', 'how do i treat this',
            'what medicine should i use', 'how should i cure this',
            'prescribe treatment', 'what is the cure',
            'how to fix this skin', 'treatment options',
            'how should i apply', 'what cream should i use',
            'how do i use the medicine', 'application instructions',
            'how often should i apply', 'dosage instructions',
            'what ointment do you recommend', 'how to use the emollient',
            
            # Ask about disease (2)
            'what is eczema', 'tell me about psoriasis',
            'what is acne', 'explain this disease',
            'information about acne', 'what is dermatitis',
            'can you explain what this condition is', 'what exactly is this',
            'describe eczema for me', 'what does psoriasis mean',
            'tell me more about this condition', 'explain this skin problem',
            
            # Ask severity (3)
            'is this serious', 'is this condition dangerous',
            'should i be worried', 'how bad is this',
            'is this normal', 'will this get worse',
            'is it severe', 'how serious is my condition',
            'should i go to hospital', 'is this an emergency',
            'will this harm me', 'can this spread to others',
            
            # Ask advice (4)
            'what else can i do', 'any lifestyle tips',
            'how can i prevent this', 'what should i avoid',
            'what foods should i eat', 'any home remedies',
            'how can i help my skin', 'what can make it better',
            'any advice for me', 'tips to improve my condition',
            'what changes should i make', 'how to manage this daily',
            
            # Ask causes (5)
            'what causes this', 'why do i have this',
            'how did i get this', 'what triggers this',
            'is this contagious', 'can others catch this',
            'is it genetic', 'is this hereditary',
            'what made this happen', 'what started this condition',
            'is it from stress', 'did food cause this',
            
            # Ask healing (6) - NEW
            'is this healing', 'am i getting better',
            'how long to heal', 'when will this go away',
            'is the treatment working', 'signs of improvement',
            'is my skin recovering', 'how do i know if its healing',
            'will this heal completely', 'healing time',
            'am i improving', 'is the rash going away',
            
            # Ask worsening (7) - NEW
            'is this getting worse', 'what if it spreads',
            'signs it is worsening', 'my condition is spreading',
            'its getting bigger', 'the rash is spreading',
            'when should i worry', 'red flags to watch',
            'should i see a doctor now', 'emergency signs',
            'what happens if untreated', 'can it spread to body',
            
            # General questions (8) - NEW
            'can you help me', 'i need help with my skin',
            'what do you think', 'your opinion',
            'tell me more', 'explain please',
            'what should i do', 'guide me',
            'any suggestions', 'what do you recommend',
            'not sure what to do', 'confused about my skin',
            
            # Other (9) - greetings, farewells, help queries, appreciation
            'hello', 'hi there', 'good morning',
            'thanks', 'okay', 'got it', 'sure',
            'what is your name', 'who are you',
            'goodbye', 'see you later', 'bye',
            'what can you do', 'how can you help me', 'what do you do',
            'how does this work', 'help me understand'
        ]
        
        training_labels = [
            # Symptoms (0) - 16 items
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            # Treatment (1) - 16 items
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            # About disease (2) - 12 items
            2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
            # Severity (3) - 12 items
            3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
            # Advice (4) - 12 items
            4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
            # Causes (5) - 12 items
            5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
            # Healing (6) - 12 items
            6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
            # Worsening (7) - 12 items
            7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
            # General (8) - 12 items
            8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
            # Other (9) - 17 items
            9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9
        ]
        
        X = self.vectorizer.fit_transform(training_texts)
        self.classifier.fit(X, training_labels)
        self.trained = True
    
    def predict(self, text: str) -> tuple[str, float]:
        """
        Predict intent and confidence
        Returns: (intent_label, confidence)
        """
        if not self.trained or not text.strip():
            return 'other', 0.0
        
        try:
            # Single text should produce shape (1, n_features)
            text_clean = text.lower().strip()
            if not text_clean:
                return 'other', 0.0
            
            X = self.vectorizer.transform([text_clean])
            pred = int(self.classifier.predict(X)[0])  # Ensure it's a Python int
            confidence = float(self.classifier.predict_proba(X)[0].max())
            intent = self.intent_map.get(pred, 'other')
            return intent, confidence
        except Exception as e:
            print(f"Intent classification error: {e}")
            return 'other', 0.0


# Global singleton
_intent_classifier = None

def get_intent_classifier() -> IntentClassifier:
    """Get or create intent classifier"""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
