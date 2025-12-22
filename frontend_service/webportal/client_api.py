import requests
from django.conf import settings


IDENTITY_URL = settings.IDENTITY_SERVICE_URL
ACCOUNT_URL = settings.ACCOUNT_SERVICE_URL
PAYMENT_URL = settings.PAYMENT_SERVICE_URL
LEDGER_URL = settings.LEDGER_SERVICE_URL

class IdentityClient:
    def __init__(self, token=None):
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def login(self, username, password):
        """Calls Identity Service to get JWT"""
        url = f"{IDENTITY_URL}/Identity_service_api/login/"
        response = requests.post(url, json={"username": username, "password": password})
        return response  # Let view handle status codes
    
    def logout(self, data):
        url = f"{IDENTITY_URL}/Identity_service_api/logout/"
        return requests.post(url, json=data, headers=self.headers)
    
    def customer_register(self, data):
        url = f"{IDENTITY_URL}/Identity_service_api/customer_register/"
        return requests.post(url, json=data, headers=self.headers)

    def staff_register(self, data):
        url = f"{IDENTITY_URL}/Identity_service_api/staff_register/"
        return requests.post(url, json=data, headers=self.headers)  


class AccountClient:   
    def __init__(self, token=None):
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    def dashboard(self):
        url = f"{ACCOUNT_URL}/account_service_api/dashboard/"
        return requests.get(url, headers=self.headers)
    
    def get_balance(self):
        """Calls Account Service"""
        url = f"{ACCOUNT_URL}/account_service_api/get_balance/"
        return requests.get(url, headers=self.headers)

    def create_bank_account(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/create_BankAccount/"
        return requests.post(url, json=data, headers=self.headers)
    
    def bank_account_details(self):
        url = f"{ACCOUNT_URL}/account_service_api/BankAccountDetails/"
        return requests.get(url, headers=self.headers)
    
    def block_account(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/block_account/"
        return requests.post(url, json=data, headers=self.headers)
    
    def staff_block_account(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/staff_block_account/"
        return requests.post(url, json=data, headers=self.headers)
    
    def create_card(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/create_card/"
        return requests.post(url, json=data, headers=self.headers)
    
    def view_cards(self):
        url = f"{ACCOUNT_URL}/account_service_api/card_details/"
        return requests.get(url, headers=self.headers)
    
    def verify_card(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/verify_card/"
        return requests.post(url, json=data, headers=self.headers)
    
    def block_card(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/block_card/"
        return requests.post(url, json=data, headers=self.headers)
    
    def loan_apply(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/loan_apply/"
        return requests.post(url, json=data, headers=self.headers)
    
    def search_loan(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/loan_operations/"
        return requests.get(url, json=data, headers=self.headers)
    
    def update_loan(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/loan_operations/"
        return requests.post(url, json=data, headers=self.headers)
    
    def loan_detail(self):
        url = f"{ACCOUNT_URL}/account_service_api/loan_detail/"
        return requests.get(url, headers=self.headers)
    
    def create_ticket(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/create_ticket/"
        return requests.post(url, json=data, headers=self.headers)

    def staff_block_account(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/staff_block_account/"
        return requests.post(url, json=data, headers=self.headers)
    
    def get_ticket(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/fetch_update_ticket/"
        return requests.get(url, json=data, headers=self.headers)
    
    def update_ticket(self, data):
        url = f"{ACCOUNT_URL}/account_service_api/fetch_update_tickets/"
        return requests.post(url, json=data, headers=self.headers)
    
    def get_bankpool_details(self):
        url = f"{ACCOUNT_URL}/account_service_api/bankpool_details/"
        return requests.get(url, headers=self.headers)
    
    def get_pending_tickets(self):
        url = f"{ACCOUNT_URL}/account_service_api/get_pendingtickets/"
        return requests.get(url, headers=self.headers)
    
    def get_pending_loans(self):
        url = f"{ACCOUNT_URL}/account_service_api/get_pendingloans/"
        return requests.get(url, headers=self.headers)
    
class PaymentClient:
    def __init__(self, token=None):
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        

    def internal_transfer(self, data):
        """Calls Payment Service"""
        url = f"{PAYMENT_URL}/payment_api/internal_transfer/"
        return requests.post(url, json=data, headers=self.headers)
    
    def card_payment(self, data):
        url = f"{PAYMENT_URL}/payment_api/card_payment/"
        return requests.post(url, json=data, headers=self.headers)
    
    def transfer_history(self):
        url = f"{PAYMENT_URL}/payment_api/transfer_history/"
        return requests.get(url, headers=self.headers)
    
    def general_history(self):
        url = f"{PAYMENT_URL}/payment_api/general_history/"
        return requests.get(url, headers=self.headers)
    

class BankClient:
    def __init__(self, token=None):
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        
    def get_bank_records(self):
        url = f"{LEDGER_URL}/ledger_api/ledger_logs/"
        return requests.get(url, headers=self.headers)
    
    def get_transactions(self):
        url = f"{LEDGER_URL}/ledger_api/transaction_logs/"
        return requests.get(url, headers=self.headers)