from rest_framework import serializers
from ..models import *


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ('PIN',)
        
class pinserializer(serializers.Serializer):
    pin = serializers.IntegerField(write_only=True, required=True)

class CardInputSerializer(serializers.Serializer):
    PIN = serializers.CharField(required=True)
    card_number = serializers.CharField(required=True)
    cvv = serializers.CharField(required=True)
        
class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ('amount', 'duration')
        
class CreateTicketSerializer(serializers.Serializer):
    subject = serializers.CharField(write_only=True, required=True)
    complaint = serializers.CharField(write_only=True, required=True)

class GetLoanSerializer(serializers.Serializer):
    account_number = serializers.CharField(write_only=True, required=True)

class UpdateLoanSerializer(serializers.Serializer):
    account_number = serializers.CharField(write_only=True, required=True)
    status = serializers.CharField(required=True)


class GetTicketSerializer(serializers.Serializer):
    ticket_id = serializers.IntegerField(write_only=True, required=True)
    
class UpdateTicketSerializer(serializers.Serializer):
    ticket_id = serializers.IntegerField(write_only=True, required=True)
    resolved = serializers.BooleanField(required=True)
    remarks = serializers.CharField(required=False)

class blockaccountserializer(serializers.Serializer):
    account_number  =serializers.CharField(required=True)
    pin = serializers.CharField(required=True)


class DebitSerializer(serializers.Serializer):
    account_number = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)


    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Debit amount must be positive.")
        return value

class CreditSerializer(serializers.Serializer):
    account_number = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Debit amount must be positive.")
        return value

class BankSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)