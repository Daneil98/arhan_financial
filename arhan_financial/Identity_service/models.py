from django.db import models
from django.contrib.auth.models import  AbstractUser, PermissionsMixin
from django.conf import settings #

# Create your models here.
"""
class user(AbstractUser):
    username = models.CharField(max_length=20, unique=True)
    id = models.AutoField(primary_key=True, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=11, unique=True)
    sex = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
    ]) 
    is_active = models.BooleanField('active status', default=True)
    REQUIRED_FIELDS = ['email', 'phone', 'first_name', 'last_name', 'sex', ]
    
    def __str__(self):
        return self.username
"""

class user(AbstractUser, PermissionsMixin):
    id = models.AutoField(primary_key=True, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=11, unique=True)
    sex = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
    ]) 
    
    is_active = models.BooleanField('active status', default=True)
    REQUIRED_FIELDS = ['email', 'phone', 'first_name', 'last_name', 'sex', ]
    
    def __str__(self):
        return self.username

    
