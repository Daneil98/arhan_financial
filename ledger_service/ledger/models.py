from django.db import models
import uuid
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Create your models here.
    
class LedgerAccount(models.Model):
    """
    Represents a financial account in the ledger system.
    This maps 1:1 to BankAccount from the account service, but only by reference ID.
    """
    ledger_id = models.UUIDField(default=uuid.uuid4, editable=False)
    user_id = models.IntegerField(help_text="ID of the User from Account Service", unique=True)
    account_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    currency = models.CharField(max_length=10, default="NGN")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"LedgerAcct({self.ledger_id}) belonging to user({self.user_id}) with of ({self.account_type} account)"


class Transaction(models.Model):
    """
    Represents a complete double-entry transaction.
    E.g., "Alice pays Bob 100 USD"
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.IntegerField(help_text="This helps pin the user initiating the transaction")
    reference = models.CharField(max_length=100, unique=True)  # idempotency key
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_reconciled = models.BooleanField(default=False)

    def __str__(self):
        return f"Txn {self.reference} by {self.user_id}"


class LedgerEntry(models.Model):
    """
    Immutable atomic movement in the ledger.
    Every Transaction has at least two LedgerEntries:
      - One DEBIT entry
      - One CREDIT entry
    """
    ENTRY_TYPE_CHOICES = [("DEBIT", "Debit"), ("CREDIT", "Credit")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.IntegerField(help_text="This helps pin user initiating the transaction")
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="entries")
    ledger_account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT)
    entry_type = models.CharField(max_length=6, choices=ENTRY_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=10, default="NGN")
    created_at = models.DateTimeField(auto_now_add=True)
    immutable_hash = models.CharField(max_length=64, editable=False, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(amount=0),
                name="non_zero_amount"
            )
        ]

    def save(self, *args, **kwargs):
        """
        Generate a hash signature (immutable fingerprint) so entries cannot be tampered with.
        """
        import hashlib, json
        raw = json.dumps({
            "transaction": str(self.transaction_id),
            "ledger_account": str(self.ledger_account_id),
            "entry_type": self.entry_type,
            "amount": str(self.amount),
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }, sort_keys=True)
        self.immutable_hash = hashlib.sha256(raw.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.entry_type} {self.amount} {self.currency} -> {self.user_id}"
