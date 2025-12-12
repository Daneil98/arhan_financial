# ledger/utils/posting.py
"""
This makes it easier for other apps (payments, wallet, savings)
to post transactions without writing logic repeatedly.
"""

from django.db import transaction as db_transaction
from ledger.models import LedgerAccount, LedgerEntry, Transaction

def post_double_entry(reference: str, description: str, debit_account_id: str, credit_account_id: str, amount):

    # Idempotency
    if Transaction.objects.filter(reference=reference).exists():
        return Transaction.objects.get(reference=reference)

    with db_transaction.atomic():
        txn = Transaction.objects.create(reference=reference, description=description)

        LedgerEntry.objects.create(
            transaction=txn,
            account_id=debit_account_id,
            entry_type="DEBIT",
            amount=amount,
        )

        LedgerEntry.objects.create(
            transaction=txn,
            account_id=credit_account_id,
            entry_type="CREDIT",
            amount=amount,
        )

    return txn
