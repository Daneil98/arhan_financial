from django.db import models
from django.contrib.auth.models import  AbstractUser, PermissionsMixin
from datetime import datetime, timedelta
import uuid


# Create your models here.

class user(AbstractUser, PermissionsMixin):
    is_accountant = models.BooleanField('accountant status', default=False)
    is_IT = models.BooleanField('IT status', default=False)
    is_account_officer = models.BooleanField('account officer status', default=False)
    is_customer = models.BooleanField('customer status', default=False)

    id = models.AutoField(primary_key=True, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    national_id = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=11, unique=True)
    sex = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
    ]) 
    
    is_active = models.BooleanField('active status', default=True)
    date_of_birth = models.DateField(null=True, blank=True)
    REQUIRED_FIELDS = ['email', 'phone', 'first_name', 'last_name', 'sex', ]
    
    def __str__(self):
        return self.username
    
"""
class CustomerIdentity(AbstractUser):
    id = models.AutoField(primary_key=True, unique=True)
    username = models.CharField('email (used as username)',max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    national_id = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=11, unique=True)
    sex = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),], default='other') 
    
    is_active = models.BooleanField('active status', default=True)
    date_of_birth = models.DateField(null=True, blank=True)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'phone', 'first_name', 'last_name', 'sex', ]

    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customer_groups',  # Unique related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customer_user_permissions',  # Unique related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username
    
    
class StaffIdentity(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=11, unique=True)
    sex = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),], default='other') 
    
    is_active = models.BooleanField('active status', default=True)
    is_staff_type = models.CharField('staff type', max_length=20, choices=[
        ('account_officer', 'Account Officer'),
        ('trader', 'Trader'),
        ('accountant', 'Accountant'),
    ])
    is_IT = models.BooleanField('IT staff status', default=False)
    date_of_birth = models.DateField(null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'phone', 'first_name', 'last_name',
                       'sex', "is_staff_type", "is_active"]
    
    
        # Add these overrides to fix the clash
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='staff_groups',  # Unique related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='staff_user_permissions',  # Unique related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username
"""


    
