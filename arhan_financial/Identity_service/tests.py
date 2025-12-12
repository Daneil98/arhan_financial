#from django.test import TestCase

# Create your tests here.
"""

dict = {'a': 1, 'b': 2, 'c': 3, '1': 4, 1: '5'}
for key in dict.keys():
    print(f'- {key}')
    
    
x = 3


print(f'Value of x is {x, "yolo"}')







"""

import django
from  Identity_service.models import user
from arhan_financial.settings import SIMPLE_JWT

from rest_framework_simplejwt.authentication import JWTAuthentication

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


CustomJWTAuthentication("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY0NDI1MzY0LCJpYXQiOjE3NjQ0MjQ0NjQsImp0aSI6IjhiMDljYzdiNzkxNTRjMzdhNjI1N2ZjMjA0MDFkNjdlIiwidXNlcl9pZCI6IjJjZjJiMTE1LTFiMjYtNDRhYy05NGFmLThkNGIwMjkxNjNmMSJ9.7B0KPFctpxbgh_FfMxL8nAbKPMSB9p6sp-3QEE4CzDQ")