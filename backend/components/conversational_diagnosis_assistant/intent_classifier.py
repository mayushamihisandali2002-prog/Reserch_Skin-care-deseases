"""
Intent Classifier for routing messages
Classifies user input into: symptom_description, ask_treatment, ask_about_disease, 
                           ask_severity, ask_advice, ask_causes, other
"""

import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

class IntentClassifier:
    """Robust intent classifier using TF-IDF (1,2-grams) + Logistic Regression"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=500,
            stop_words='english',
            lowercase=True
        )
        self.classifier = LogisticRegression(C=1.0, max_iter=200)
        self.intent_map = {
            0: 'symptom_description',
            1: 'ask_treatment',
            2: 'ask_about_disease',
            3: 'ask_severity',
            4: 'ask_advice',
            5: 'ask_causes',
            6: 'ask_healing',
            7: 'ask_worsening',
            8: 'ask_skin_type',
            9: 'general_question',
            10: 'other'
        }
        self.trained = False
        self._train()
    
    def _train(self):
        """Train on synthetic intent dataset"""
        
        # Synthetic training data - expanded for significantly better coverage
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
            'i have a lot of whiteheads', 'my face is very oily',
            'extreme itching at night', 'scaly red patches on my elbows',
            'sudden breakout of pimples', 'rash that burns and itches',
            'inflamed patches of skin', 'my skin is cracking and bleeding',
            'itchy red welts appearing suddenly', 'skin feels very rough and dry',
            'lots of blackheads on my nose', 'my hands are very dry and red',
            'i have dark brown spots on my face', 'noticed melasma on my forehead',
            'flat darkened patches of skin', 'sun damage spots appearing',
            'i have a circular ring rash on my arm', 'circular red patch on my leg',
            'flushing and redness on my cheeks', 'face is red and blushing',
            'painful strip of blisters on my back', 'band of painful bumps on my waist',
            'white patches on my hands', 'losing skin color in spots',
            'honey colored crust around my mouth', 'yellow scabs on my face',
            'pearly bumps on my torso', 'small dome shaped marks',
            'red bumps around my hair follicles', 'itchy scalp and hair bulbs',
            'intense itching between fingers', 'rash that is worse at night',
            'rough cauliflower like bump on my finger', 'hard grainy growth on foot',
            'dandruff and greasy scale on scalp', 'yellow flakes on eyebrows',
            'purple itchy bumps on my wrist', 'polygon shaped purple rash',
            'red hot swollen skin that is tender', 'spreading red rash and fever',
            'cold sores on my lip', 'tingling blisters near mouth',
            'discolored patches on my chest', 'light spots on my back',
            
            # Ask treatment (1)
            'what is the treatment', 'how do i treat this',
            'what medicine should i use', 'how should i cure this',
            'prescribe treatment', 'what is the cure',
            'how to fix this skin', 'treatment options',
            'how should i apply', 'what cream should i use',
            'how do i use the medicine', 'application instructions',
            'how often should i apply', 'dosage instructions',
            'what ointment do you recommend', 'how to use the emollient',
            'give me a treatment plan', 'what is the best medicine for eczema',
            'how do i get rid of acne', 'remedy for itchy skin',
            'which cream is effective', 'medication for psoriasis',
            'what should i put on this rash', 'how to stop the itching',
            'medical advice for my skin', 'best way to heal this',
            
            # Ask about disease (2)
            'what is eczema', 'tell me about psoriasis',
            'what is acne', 'explain this disease',
            'information about acne', 'what is dermatitis',
            'can you explain what this condition is', 'what exactly is this',
            'describe eczema for me', 'what does psoriasis mean',
            'tell me more about this condition', 'explain this skin problem',
            'definition of urticaria', 'causes and symptoms of acne',
            'how does dermatitis look like', 'facts about skin diseases',
            'more info on psoriasis', 'condition details',
            'what causes dark spots on skin', 'understand skin pigmentation',
            'what is ringworm', 'tell me about rosacea', 'what are shingles',
            'explain fungal infections', 'information about shingles rash',
            'what is vitiligo', 'how does impetigo happen', 'what is molluscum',
            'tell me about folliculitis', 'what are scabies', 'what is a verruca',
            'explain seborrheic dermatitis', 'what is lichen planus',
            'information on cellulitis', 'tell me about cold sores',
            'what is tinea versicolor', 'pityriasis versicolor info',
            
            # Ask severity (3)
            'is this serious', 'is this condition dangerous',
            'should i be worried', 'how bad is this',
            'is this normal', 'will this get worse',
            'is it severe', 'how serious is my condition',
            'should i go to hospital', 'is this an emergency',
            'will this harm me', 'can this spread to others',
            'is it life threatening', 'do i need a doctor immediately',
            'signs of a serious infection', 'how urgent is this',
            'is the redness dangerous', 'emergency symptoms to watch for',
            'should i seek medical help', 'is this a critical issue',
            
            # Ask advice (4)
            'what else can i do', 'any lifestyle tips',
            'how can i prevent this', 'what should i avoid',
            'what foods should i eat', 'any home remedies',
            'how can i help my skin', 'what can make it better',
            'any advice for me', 'tips to improve my condition',
            'what changes should i make', 'how to manage this daily',
            'preventing future breakouts', 'diet for clear skin',
            'best skincare routine for me', 'natural ways to treat itching',
            'how to avoid triggers', 'lifestyle changes for psoriasis',
            'skin care tips for dermatitis', 'recommendations for healthy skin',
            
            # Ask causes (5)
            'what causes this', 'why do i have this',
            'how did i get this', 'what triggers this',
            'is this contagious', 'can others catch this',
            'is it genetic', 'is this hereditary',
            'what made this happen', 'what started this condition',
            'is it from stress', 'did food cause this',
            'origin of this rash', 'reasons for sudden acne',
            'is it an allergic reaction', 'common triggers for eczema',
            'why is my skin reacting this way', 'environmental causes',
            'genetic factors in skin disease', 'is it from a virus',
            
            # Ask healing (6)
            'is this healing', 'am i getting better',
            'how long to heal', 'when will this go away',
            'is the treatment working', 'signs of improvement',
            'is my skin recovering', 'how do i know if its healing',
            'will this heal completely', 'healing time',
            'am i improving', 'is the rash going away',
            'duration of recovery', 'speeding up healing',
            'estimated time for clear skin', 'is it resolving',
            'progress update on my skin', 'how to track healing',
            
            # Ask worsening (7)
            'is this getting worse', 'what if it spreads',
            'signs it is worsening', 'my condition is spreading',
            'its getting bigger', 'the rash is spreading',
            'when should i worry', 'red flags to watch',
            'should i see a doctor now', 'emergency signs',
            'what happens if untreated', 'can it spread to body',
            'increasing pain or redness', 'is the infection spreading',
            'warning signs of complication', 'deteriorating skin condition',
            'what if the treatment fails', 'complications to avoid',
            
            # Ask skin type / routine (8)
            'what is my skin type', 'how to find skin type',
            'do i have oily skin', 'is my skin dry',
            'combination skin routine', 'skincare routine for me',
            'best products for my skin type', 'how to care for oily skin',
            'daily routine for dry skin', 'should i use a cleanser',
            'recommend a moisturizer', 'skin care for teenagers',
            'how to manage combination skin', 'steps for healthy skin',
            'morning skincare routine', 'nighttime skin routine',
            
            # General questions (9)
            'can you help me', 'i need help with my skin',
            'what do you think', 'your opinion',
            'tell me more', 'explain please',
            'what should i do', 'guide me',
            'any suggestions', 'what do you recommend',
            'not sure what to do', 'confused about my skin',
            'give me your thoughts', 'how should i proceed',
            'need some guidance', 'your expert opinion',
            'what are my options', 'help me understand my skin',
            
            # Other (10) - greetings, farewells, help queries, appreciation
            'hello', 'hi there', 'good morning',
            'thanks', 'okay', 'got it', 'sure',
            'what is your name', 'who are you',
            'goodbye', 'see you later', 'bye',
            'what can you do', 'how can you help me', 'what do you do',
            'how does this work', 'help me understand',
            'nice to meet you', 'thank you very much', 'see ya',
            'cool', 'awesome', 'understood', 'i see',
            'how are you', 'tell me a joke', 'who made you'
        ]
        
        training_labels = (
            [0] * 60 +  # Symptom descriptions
            [1] * 26 +  # Ask treatment
            [2] * 37 +  # Ask about disease
            [3] * 20 +  # Ask severity
            [4] * 20 +  # Ask advice
            [5] * 20 +  # Ask causes
            [6] * 18 +  # Ask healing
            [7] * 18 +  # Ask worsening
            [8] * 16 +  # Ask skin type
            [9] * 18 +  # General questions
            [10] * 27   # Other
        )

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
