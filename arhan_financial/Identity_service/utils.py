# your_app/auth/backends.py (corrected)

import uuid
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
# Import settings to access SIMPLE_JWT configuration
from rest_framework_simplejwt.settings import api_settings 

User = get_user_model()

class UUIDSafeJWTAuthentication(JWTAuthentication):
    # 🎯 FIX 1: Explicitly define the attribute needed by the parent class/logic
    # This retrieves the value set in settings.py (default is 'user_id')
    user_id_claim = api_settings.USER_ID_CLAIM
    """
    def get_user(self, validated_token):
        # ... validation and UUID conversion logic ...
        
        try:
            user_uuid = uuid.UUID(str(self.user_id_claim))
        except ValueError:
            return None
        
        try:
            # ⭐ CRITICAL CHANGE: Use the explicit field name 'id' instead of 'pk'
            user = User.objects.get(id=user_uuid) 
        except User.DoesNotExist:
            return None
            
        return user
    """
def get_user(self, validated_token):
        try:
            user_id = validated_token[self.user_id_claim]
            # CRITICAL: Force conversion to UUID object here
            user_uuid = uuid.UUID(str(user_id))
        except (KeyError, ValueError):
            return None
        
        try:
            # Look up using the ID field and the UUID object
            # If the user model is correctly defined with UUID primary_key=True, this works.
            return User.objects.get(pk=user_uuid) 
        except User.DoesNotExist:
            return None