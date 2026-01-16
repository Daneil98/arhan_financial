import requests
from payments import settings
import jwt # Make sure you have PyJWT installed (pip install PyJWT)
import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings
import time

ACCOUNT_SERVICE_BASE_URL = 'http://account:8002'   # Docker internal
FRAUD_SERVICE_BASE_URL = 'http://fraud:8006'    #Docker internal


# 1. SETUP PERSISTENT SESSION 
# This opens a connection pool. The first call takes 100ms, but the next calls (Debit/Credit) take ~10ms.

def get_session():
    session = requests.Session()
    
    # Optional: Add automatic retries for network blips
    retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    return session


# Initialize it once when the worker starts (Each Celery worker process will have its own session)
account_service_session = get_session()

fraud_service_session = get_session()


def check_for_fraud(transaction_data):
    """
    Calls the FastAPI Fraud Microservice synchronously.
    
    Args:
        transaction_data (dict): Dictionary containing:
            - transaction_id (str)
            - user_id (str)
            - amount (float/str)
            - account_type (str)
            - currency (str)
            - timestamp (float, optional)

    Returns:
        dict: {
            "is_fraud": bool, 
            "risk_score": float, 
            "reason": str
        }
    """
    url = f"{FRAUD_SERVICE_BASE_URL}/check/"
    
    # Prepare payload conformant to FastAPI schema
    payload = {
        "transaction_id": str(transaction_data.get("transaction_id", "unknown")),
        "user_id": str(transaction_data.get("user_id", "unknown")),
        "amount": float(transaction_data.get("amount", 0.0)),
        "currency": str(transaction_data.get("currency", "NGN")),
        "timestamp": float(transaction_data.get("timestamp", time.time()))
    }
    
    try:
        # Short timeout because we don't want to block the payment flow for long
        response = requests.post(url, json=payload, timeout=2) 
        
        if response.status_code == 200:
            return response.json() 
        
        print(f"Fraud Service Error {response.status_code}: {response.text}")
        # Fail Open: If service errors, we assume it's NOT fraud to avoid blocking legitimate users
        return {"is_fraud": False, "risk_score": 0.0, "reason": "Service Error (Fail Open)"}
        
    except requests.exceptions.ConnectionError:
        print(f"Fraud Service Unreachable at {url}")
        return {"is_fraud": False, "risk_score": 0.0, "reason": "Service Unreachable"}
        
    except Exception as e:
        print(f"Fraud Check Failed: {e}")
        return {"is_fraud": False, "risk_score": 0.0, "reason": f"Client Error: {str(e)}"}


def generate_service_token(user_id):
    """
    Generates a valid, short-lived JWT for internal service calls.
    """
    payload = {
        'token_type': 'access',
        'user_id': str(user_id), # Impersonate the user involved in the tx
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=60), # Expire in 60s
        'iat': datetime.datetime.utcnow(),
        'jti': 'service-call-' + str(datetime.datetime.utcnow().timestamp())
    }
    
    # Sign it with the Shared Secret
    token = jwt.encode(payload, settings.JWT_SHARED_SECRET, algorithm='HS256')
    
    # If using newer PyJWT versions, encode returns a string. 
    # In older versions it returned bytes, so we decode just in case:
    if isinstance(token, bytes):
        token = token.decode('utf-8')
        
    return token


def verify_card(user_id, card_number, cvv, PIN):
    url = f"{ACCOUNT_SERVICE_BASE_URL}/account_service_api/verify_card/"
    payload = {
        "user_id": user_id,
        "card_number": card_number,
        "cvv": cvv,
        "PIN": PIN,
    }
    # 1. Generate a real token
    token = generate_service_token(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",  # <--- Use the generated token
        "Content-Type": "application/json"
    }
    try:
        response = account_service_session.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Verify Card Error: {e}")
        return {"validity": False, "error": str(e)}


def verify_pin(user_id, account_number, pin):
    url = f"{ACCOUNT_SERVICE_BASE_URL}/account_service_api/verify_AccountPin/"
    token = generate_service_token(user_id)
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"account_number": account_number, "pin": pin,}

    try:
        # USE THE SESSION OBJECT INSTEAD OF 'requests'
        response = account_service_session.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Verify Pin Error: {e}")
        return {"validity": False, "error": str(e)}
    
def debit_bank(user_id, amount):
    url = f"{ACCOUNT_SERVICE_BASE_URL}/account_service_api/debit_bank/"
    payload = {
        "amount": str(amount),
    }
    # 1. Generate a real token
    token = generate_service_token(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",  # <--- Use the generated token
        "Content-Type": "application/json"
    }
    try:
        response = account_service_session.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            return {"status": "success"}
        return {"status": "failed", "message": response.text}
    except Exception as e:
        return {"status": "failed", "message": str(e)}
    
    
def credit_bank(user_id, amount):
    url = f"{ACCOUNT_SERVICE_BASE_URL}/account_service_api/credit_bank/"
    payload = {
        "amount": str(amount),
    }
    # 1. Generate a real token
    token = generate_service_token(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",  # <--- Use the generated token
        "Content-Type": "application/json"
    }
    try:
        response = account_service_session.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            return {"status": "success"}
        return {"status": "failed", "message": response.text}
    except Exception as e:
        return {"status": "failed", "message": str(e)}

def debit_account(user_id, account_id, amount):
    url = f"{ACCOUNT_SERVICE_BASE_URL}/account_service_api/debit/"
    payload = {
        "amount": str(amount),
        "account_number": account_id,
        "user_id": user_id,
    }
    # 1. Generate a real token
    token = generate_service_token(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",  # <--- Use the generated token
        "Content-Type": "application/json"
    }
    try:
        response = account_service_session.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            return {"status": "success"}
        return {"status": "failed", "message": response.text}
    except Exception as e:
        return {"status": "failed", "message": str(e)}

def credit_account(user_id, account_id, amount): 
    # Logic implies payee usually receives into savings or current? 
    # You might need to add payee_account_type to your serializer later.
    url = f"{ACCOUNT_SERVICE_BASE_URL}/account_service_api/credit/"
    payload = {
        "amount": str(amount),
        "user_id": user_id,
        "account_number": account_id,
        #"account_type": account_type
    }
    # 1. Generate a real token
    token = generate_service_token(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",  # <--- Use the generated token
        "Content-Type": "application/json"
    }
    try:
        response = account_service_session.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            return {"status": "success"}
        return {"status": "failed", "message": response.text}
    except Exception as e:
        return {"status": "failed", "message": str(e)}