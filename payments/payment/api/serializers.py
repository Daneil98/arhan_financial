from rest_framework import serializers
from ..models import PaymentRequest


class PaymentCreateSerializer(serializers.Serializer):
    payer_account_id = serializers.CharField(required=True)
    payee_account_id = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    currency = serializers.CharField(required=True)
    payment_type = serializers.CharField(required=True)
    account_type = serializers.CharField(required=True)
    pin = serializers.IntegerField(required=True)


class CardPaymentSerializer(serializers.Serializer):
    payee_account_id = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    currency = serializers.CharField(required=True)
    payment_type = serializers.CharField(required=True)
    card_number = serializers.CharField(required=True)
    cvv = serializers.IntegerField(required=True)
    PIN = serializers.IntegerField(required=True)