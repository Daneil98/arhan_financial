#from django.test import TestCase

# Create your tests here.
import django
from  Identity_service.models import user
from arhan_financial.settings import SIMPLE_JWT
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from .models import user

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            # Check this line in the library's or your custom code
            # It must be filtering by the UUID primary key field
            user_id = validated_token[SIMPLE_JWT.USER_ID_CLAIM]
            
            # Make sure this lookup works with a UUID:
            user = user.objects.get(pk=user_id) 
            
        except user.DoesNotExist:
            return None
        
        return user


User = get_user_model()

class IdentityTests(APITestCase):

    @patch('Identity_service.tasks.publish_customer_created.apply_async')
    def test_customer_registration(self, mock_publish_task):
        """
        Test that registering a customer creates User, Profile, and triggers event.
        """
        url = reverse('Identity_service_api:customer_register') # Check your namespace/name
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "08012345678",
            "sex": "male",
            "date_of_birth": "1990-01-01"
        }

        response = self.client.post(url, data, format='json')

        # 1. Assert API Success
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 2. Assert Data Integrity
        self.assertTrue(User.objects.filter(email="new@example.com").exists())
        self.assertTrue(user.objects.filter(phone="08012345678").exists())
        
        user = User.objects.get(email="new@example.com")
        self.assertEqual(user.role, 'customer')

        # 3. Assert Event Published
        mock_publish_task.assert_called_once()
        task_data = mock_publish_task.call_args[1]['args'][0]
        self.assertEqual(task_data['email'], "new@example.com")


CustomJWTAuthentication("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY0NDI1MzY0LCJpYXQiOjE3NjQ0MjQ0NjQsImp0aSI6IjhiMDljYzdiNzkxNTRjMzdhNjI1N2ZjMjA0MDFkNjdlIiwidXNlcl9pZCI6IjJjZjJiMTE1LTFiMjYtNDRhYy05NGFmLThkNGIwMjkxNjNmMSJ9.7B0KPFctpxbgh_FfMxL8nAbKPMSB9p6sp-3QEE4CzDQ")