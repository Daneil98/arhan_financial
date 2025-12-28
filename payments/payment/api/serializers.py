from rest_framework import serializers
from ..models import PaymentRequest


class PaymentCreateSerializer(serializers.Serializer):
    payee_account_id = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    pin = serializers.IntegerField(required=True)


class CardPaymentSerializer(serializers.Serializer):
    payee_account_id = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    card_number = serializers.CharField(required=True)
    cvv = serializers.IntegerField(required=True)
    pin = serializers.IntegerField(required=True)