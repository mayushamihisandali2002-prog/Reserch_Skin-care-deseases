import pandas as pd
import random

def add_records():
    csv_path = "assets/data/treatment_records_clean.csv"
    try:
        df = pd.read_csv(csv_path)
        last_case_id = df["case_id"].max()
        
        diseases = [
            "Melasma", 
            "Freckles (Ephelides)", 
            "Solar Lentigines (Sunspots)", 
            "Post-inflammatory hyperpigmentation"
        ]
        
        medicines = [
            ("Vitamin C Serum", "yes"),
            ("Niacinamide 10%", "yes"),
            ("Azelaic Acid 10%", "yes"),
            ("Retinol 0.5%", "no"),
            ("Hydroquinone 2%", "no"),
            ("Kojic Acid Cream", "yes"),
            ("Glycolic Acid Peel", "no"),
            ("Sunscreen SPF 50+", "yes")
        ]
        
        severities = ["mild", "moderate", "severe"]
        outcomes = ["improved", "improved", "improved", "no_change"] # Generally improves if treated
        
        new_records = []
        for i in range(1, 201): # Add 200 records
            disease = random.choice(diseases)
            severity = random.choice(severities)
            med, otc = random.choice(medicines)
            outcome = random.choice(outcomes)
            
            new_records.append({
                "case_id": last_case_id + i,
                "patient_id": random.randint(1000, 9999),
                "primary_disease": disease,
                "disease_category": "pigmentary",
                "severity": severity,
                "recommended_medicine": med,
                "is_over_the_counter": otc,
                "follow_up_required": random.choice(["yes", "no"]),
                "treatment_outcome": outcome
            })
            
        new_df = pd.DataFrame(new_records)
        new_df.to_csv(csv_path, mode="a", header=False, index=False)
        print(f"[Done] Added {len(new_records)} hyperpigmentation treatment records to {csv_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_records()
