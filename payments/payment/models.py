from django.db import models
import uuid
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Create your models here.


class PaymentAccount(models.Model):
    """
    This is the account that actually holds money.
    Think of it like a wallet or core-banking account.
    """
    user_id = models.IntegerField("ID from Identity_service")
    account_number = models.CharField(max_length=20, unique=True,)
    currency = models.CharField(max_length=4, default="NGN")

    def __str__(self):
        return f"PaymentAccount({self.user_id})"
    

class PaymentRequest(models.Model):
    PAYMENT_TYPES = [
        ("INTERNAL", "Internal Transfer"),
        ("CARD", "Card Payment"),
        ("BANK_EXTERNAL", "External Bank Transfer")
    ]
    
    """
    Represents a user's intention to move funds.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payer_account_id = models.IntegerField(help_text="BankAccount number (Account Service)")
    payee_account_id = models.IntegerField(help_text="BankAccount number (Account Service)")
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=10, default="NGN")
    
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    status = models.CharField(
        max_length=20,
        choices=[("PENDING", "Pending"), ("SUCCESS", "Success"), ("FAILED", "Failed")],
        default="PENDING",
    )
    
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.reference} - {self.status}"