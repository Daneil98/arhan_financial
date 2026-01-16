from fastapi import FastAPI, HTTPException, status
from .schemas import TransactionData, FraudCheckResponse
from .model import detector

app = FastAPI(title="Arhan Fraud Detection Service")

@app.get("/")
def health_check():
    return {"status": "active", "service": "fraud-detection"}

@app.post("/check/", response_model=FraudCheckResponse)
def check_transaction(data: TransactionData):
    print(f"Analyzing Transaction: {data.amount} for User {data.user_id}")
    
    # Run inference
    is_fraud, score, reason = detector.predict(data.dict())
    
    if is_fraud:
        print(f"FRAUD DETECTED: {reason}")
    else:
        print(f"Transaction Safe (Score: {score:.2f})")

    return {
        "is_fraud": is_fraud,
        "risk_score": score,
        "reason": reason
    }