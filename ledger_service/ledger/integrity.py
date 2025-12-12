# ledger/utils/integrity.py

from ledger.models import Transaction, LedgerEntry
from decimal import Decimal

def check_ledger_integrity():
    issues = []

    for txn in Transaction.objects.all():
        entries = txn.entries.all()
        if entries.count() < 2:
            issues.append(f"Txn {txn.reference} has fewer than 2 entries")

        debit_sum = sum(e.amount for e in entries if e.entry_type == "DEBIT")
        credit_sum = sum(e.amount for e in entries if e.entry_type == "CREDIT")

        if debit_sum != credit_sum:
            issues.append(
                f"Txn {txn.reference} not balanced: DEBIT={debit_sum}, CREDIT={credit_sum}"
            )

    return issues
