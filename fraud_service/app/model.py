import random

class FraudDetector:
    def __init__(self):
        pass

    def predict(self, data: dict):
        """
        Returns (is_fraud, risk_score, reason)
        """
        amount = data.get("amount", 0)
        
        # --- RULE 1: High Amount Check (Heuristic) ---
        if amount > 1000000:
            return True, 0.99, "Amount exceeds global safety limit"

        # --- RULE 2: Suspicious Round Numbers (Heuristic) ---
        if amount % 1000 == 0 and amount > 10000:
             # Add some randomness to simulate ML probability
            if random.random() > 0.8: 
                return True, 0.85, "Suspicious round number pattern"

        # --- RULE 3: Random ML Simulation ---
        risk_score = random.uniform(0, 0.4) # Mostly low risk
        
        if risk_score > 0.8:
            return True, risk_score, "ML Model Anomaly Detected"
            
        return False, risk_score, "Transaction appears normal"

# Singleton instance
detector = FraudDetector()