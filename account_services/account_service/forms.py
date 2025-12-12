from django import forms
from .models import *
from django.forms import DateInput

#BANK ACCOUNT CREATION FORMS
class SavingsAccountForm(forms.ModelForm):
    class Meta:
        model = SavingsAccount
        fields = ('PIN',)

class CurrentAccountForm(forms.ModelForm):
    class Meta:
        model = SavingsAccount
        fields = ('PIN',)
        
class CreateCardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ('PIN',)
        

class LoanApplicationForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ('amount', 'duration',)
        widgets = {
            'duration': forms.Select(choices=[
                ('3 Months', '3 Months'),
                ('6 Months', '6 Months'),
                ('12 Months', '12 Months'),
                ('24 Months', '24 Months'),
            ])
        }

#IT SUPPORT TICKET FORMS
class CreateTicketForm(forms.ModelForm):
    class Meta:
        model = IT_Tickets
        fields = ('complaint',)
        
        
class HandlingTicketForm(forms.ModelForm):
    class Meta:
        model = IT_Tickets
        fields = ('taken', 'resolved', 'remarks')
        