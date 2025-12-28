from django import forms
from django.core.exceptions import ValidationError

# Options for dropdowns


STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

DURATION_CHOICES = [
    ('1 Month', '1 Month'),
    ('3 Months', '3 Months'),
    ('6 Months', '6 Months'),
    ('12 Months', '12 Months'),
    ('24 Months', '24 Months'),
]

SUBJECT_CHOICES = [
    ('transaction', 'Transaction'),
    ('account', 'Account'),
    ('card', 'Card'),
    ('loan', 'Loan'),
    ('other', 'Other'),
]

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    
class UserRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    phone = forms.CharField(max_length=15)
    sex = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')])
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)
    
    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords dont match.')
        return cd['password2']
        
class BankAccountForm(forms.Form):
    # Serializer had fields = ('PIN',), assuming this is for creation/validation
    PIN = forms.CharField(
        label="Set Account PIN",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '4-digit PIN'}),
        max_length=4,
        required=True
    )

class AccountPinForm(forms.Form):
    """Used for generic PIN verification"""
    pin = forms.IntegerField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter PIN'}),
        required=True
    )

class CardForm(forms.Form):
    """Form for creating a new card"""
    pin = forms.CharField(
        label="Card PIN",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        max_length=4,
        required=True
    )

class CardInputForm(forms.Form):
    """Form for validating or using card details"""
    card_number = forms.CharField(
        max_length=16, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '16-digit Card Number'})
    )
    cvv = forms.CharField(
        max_length=3, 
        label="CVV",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '3 digits'})
    )
    pin = forms.CharField(
        label="PIN",
        max_length=4,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class LoanApplicationForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class CreateTicketForm(forms.Form):
    subject = forms.ChoiceField(
        choices=SUBJECT_CHOICES,
        widget = forms.Select(attrs={'class': 'form-control'})
    )
    complaint = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your issue...'}),
        required=True
    )

class GetLoanForm(forms.Form):
    account_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Number'}),
        required=True
    )

class UpdateLoanForm(forms.Form):
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class GetTicketForm(forms.Form):
    ticket_id = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ticket ID'}),
        required=True
    )

class UpdateTicketForm(forms.Form):
    resolved = forms.BooleanField(
        required=False, 
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

class StaffBlockAccountForm(forms.Form):
    account_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    pin = forms.IntegerField(
        label="Enter PIN to confirm block",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class BlockAccountForm(forms.Form):
    pin = forms.IntegerField(
        label="Enter PIN to confirm block",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
class BlockCardForm(forms.Form):
    pin = forms.IntegerField(
        label="Enter PIN to confirm block",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class DebitForm(forms.Form):
    account_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError("Debit amount must be positive.")
        return amount

class CreditForm(forms.Form):
    account_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError("Credit amount must be positive.")
        return amount

class BankForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

class InternalTransferForm(forms.Form):
    """For Internal Transfers"""
    payee_account_id = forms.CharField(
        label="To Account",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    pin = forms.IntegerField(
        label="Account PIN",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class CardPaymentForm(forms.Form):
    """For External Card Payments"""
    payee_account_id = forms.CharField(
        label="Beneficiary Account",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    card_number = forms.CharField(
        max_length=16,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Card Number'})
    )
    cvv = forms.IntegerField(
        label="CVV",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '123'})
    )
    pin = forms.IntegerField(
        label="Card PIN",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
class LoanSearchForm(forms.Form):
    account_number = forms.CharField(
        label="Account Number",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )