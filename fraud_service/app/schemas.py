from pydantic import BaseModel
from typing import Optional

class TransactionData(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    currency: str
    timestamp: float

class FraudCheckResponse(BaseModel):
    is_fraud: bool
    risk_score: float
    reason: Optional[str] = None