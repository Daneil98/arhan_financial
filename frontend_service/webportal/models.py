from django.db import models

# Create your models here.

class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    role = models.CharField(max_length=100, choices=[
        ('customer', 'customer'),
        ('staff', 'staff'),]
    )
    