from django.db import models
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import uuid
from django.conf import settings
from decimal import Decimal


# Create your models here.

class Account(models.Model):
    """
    Represents an internal bank account record that maps
    to an Identity Service user and an external Ledger account.
    """
    #ledger_id = models.UUIDField(unique=True, help_text="UUID from Ledger Service", blank=True)
    
    user_id = models.IntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=20, choices=[
        ('customer', 'Customer'),
        ('staff', 'Staff'),
    ],)

    def __str__(self):
        return f"Account with Identity ID {self.user_id}"
    
class BankAccount(models.Model):
    #ledger_id = models.UUIDField(unique=True, help_text="UUID from Ledger Service")
    user_id = models.IntegerField(unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)
    account_number = models.CharField(max_length=20, unique=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    currency = models.CharField(max_length=3, default="NGN")
    PIN = models.CharField(max_length=128)
    active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)      
    
    class Meta:
        verbose_name = "Current Account"
        verbose_name_plural = "Current Accounts"  

    def __str__(self):
        return f"Current Account {self.account_number} for {self.user_id} with balance {self.balance}"


class BankPool(models.Model):
    total_funds = models.DecimalField(max_digits=15, decimal_places=2, default=9999999999999)
    last_updated = models.DateField(auto_now=True)

    def __str__(self):
        return f"Bank Pool with total funds: {self.total_funds}"

class Card(models.Model):
    user_id = models.IntegerField(unique=True)
    card_number = models.CharField(max_length=128, unique=True)
    card_type = models.CharField(max_length=10, choices=[
        ('debit', 'Debit'),
    ], default='debit')
    expiration_date = models.DateField(default=datetime.now() + timedelta(days=365*3))  # 3 years from now
    cvv = models.CharField(max_length=255, unique=True)
    PIN = models.CharField(max_length=255, unique=True)
    issued_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.bank_account :
            raise ValueError("Card must be linked to an account.")
        super().save(*args, **kwargs)

    @property
    def account(self):
        # Helper to get whichever one exists
        return self.bank_account 

    def __str__(self):
        return f"{self.card_type.capitalize()} Card {self.card_number} for {self.user_id}"

class Loan(models.Model):
    user_id = models.IntegerField(unique=True)
    loan_id = models.UUIDField(primary_key=True, default = uuid.uuid4, help_text="Loan ID", editable=False)
    account_number = models.CharField(max_length=20, unique=True)
    monthly_repayment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_to_repay = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="NGN")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12)
    duration = models.CharField(
            max_length=15, 
            choices=[
                ('1 Month', '1 Month'),
                ('3 Months', '3 Months'),
                ('6 Months', '6 Months'),
                ('12 Months', '12 Months'),
                ('24 Months', '24 Months'),
            ], 
            default='1 Month')
    start_date = models.DateField(null=True, blank=True)
    
    end_date = models.DateField(null=True, blank=True) 
    loan_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    paid_off = models.BooleanField(default=False)

    #Add a clean string representation
    def __str__(self):
        return f"{self.loan_status} Loan of {self.amount}, owned by {self.user_id} for {self.duration} from {self.start_date} to {self.end_date}" 
    
    def save(self, *args, **kwargs):
        # 1. Parse Duration
        try:
            months = int(self.duration.split(' ')[0])
        except (ValueError, IndexError):
            months = 1 # Default fallback

        # 2. ALWAYS Calculate Repayment Details (regardless of status)
        # Convert interest rate to a multiplier (e.g. 12% -> 0.12)
        interest_multiplier = self.interest_rate / Decimal(100)
        
        # Calculate Total Repayment: Principal + (Principal * Interest)
        self.amount_to_repay = self.amount * (1 + interest_multiplier)
        
        # Calculate Monthly Payment
        self.monthly_repayment = self.amount_to_repay / Decimal(months)

        # 3. Handle Dates based on Status
        if self.loan_status == 'approved' and not self.start_date:
            # Only set start date if approved and not already set
            self.start_date = datetime.now().date()
            self.end_date = self.start_date + relativedelta(months=+months)
        elif self.loan_status == 'pending':
            # Keep dates null until approval
            self.start_date = None
            self.end_date = None

        super().save(*args, **kwargs)
    
class IT_Tickets(models.Model):
    user_id = models.IntegerField(unique=True)
    id = models.AutoField(primary_key=True, unique=True)
    subject = models.CharField(max_length=255,choices=[
        ('transaction', 'Transaction'),
        ('account', 'Account'),
        ('card', 'Card'),
        ('loan', 'Loan'),
        ('other', 'Other'),
    ],)
    complaint = models.TextField()
    resolved = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Ticket {self.id} - Taken: {self.taken} - Resolved: {self.resolved}"