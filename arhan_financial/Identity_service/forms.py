from django import forms
from .models import *
from socket import fromshare
from django.forms.widgets import DateInput, TimeInput
from django.utils.translation import gettext_lazy as _



#USER ACCOUNT FORMS
class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)
    class Meta:
        model = user
        fields = ('first_name', 'last_name', 'username', 'sex', 'date_of_birth', 'phone')
        widgets = {
            'date_of_birth': DateInput(attrs={'type': 'date'})
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords dont match.')
        return cd['password2']
    
class StaffRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)
    class Meta:
        model = user
        fields = ('first_name', 'last_name', 'username', 'email', 'sex',
                  'date_of_birth', 'phone',)
        widgets = {
            'date_of_birth': DateInput(attrs={'type': 'date'}),
        }
    

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords dont match.')
        return cd['password2']


#USER EDIT FORM        
class UserEditForm(forms.ModelForm):
    class Meta:
        model = user
        fields = ('phone', 'email',)

class StaffEditForm(forms.ModelForm):
    class Meta:
        model = user
        fields = ('phone', 'email',)
      





        