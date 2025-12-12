# ledger/serializers.py

from rest_framework import serializers
from ..models import *

class LedgerAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerAccount
        fields = ["id", "external_account_id", "name", "currency", "created_at"]


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = ["id", "transaction", "account", "entry_type", "amount", "created_at"]


class TransactionSerializer(serializers.ModelSerializer):
    entries = LedgerEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = ["id", "reference", "description", "entries", "created_at"]
