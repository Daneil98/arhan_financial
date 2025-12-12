from rest_framework import serializers
from ..models import *
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class SavingsAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsAccount
        fields = ('PIN',)
    
class CurrentAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentAccount
        fields = ('PIN',)
        
class accountserializers(serializers.Serializer):
    account_type = serializers.CharField(write_only=True, required=True)
    pin = serializers.IntegerField(write_only=True, required=True)
        
class CardSerializer(serializers.Serializer):
    account_type = serializers.CharField(label='savings or current', write_only=True, required=True)
    pin = serializers.CharField(write_only=True, required=True)
        
class CardInputSerializer(serializers.Serializer):
    PIN = serializers.CharField(required=True)
    card_number = serializers.CharField(required=True)
    cvv = serializers.CharField(required=True)
    
        
class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ('amount', 'duration')
        
class CreateTicketSerializer(serializers.Serializer):
    complaint = serializers.CharField(write_only=True, required=True)
    

class GetLoanSerializer(serializers.Serializer):
    user_id = serializers.CharField(write_only=True, required=True)

class UpdateLoanSerializer(serializers.Serializer):
    user_id = serializers.CharField(write_only=True, required=True)
    status = serializers.CharField(required=True)

class UpdateTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = IT_Tickets
        fields = ['resolved', 'remarks']
        
class accountserializer(serializers.Serializer):
    account_type = serializers.CharField(label='savings or current', write_only=True, required=True)
    pin = serializers.IntegerField(write_only=True, required=True)
    
class DebitSerializer(serializers.Serializer):
    account_number = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    account_type = serializers.ChoiceField(choices=['savings', 'current'])

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Debit amount must be positive.")
        return value

class CreditSerializer(serializers.Serializer):
    account_number = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    account_type = serializers.ChoiceField(choices=['savings', 'current'])

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Debit amount must be positive.")
        return value

class BankSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)