from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

def get_custom_claims(user):
    """
    Helper function: Extracts roles/flags from the User instance.
    Adjust the logic below to match your specific User model fields.
    """
    claims = {}
    
    # OPTION A: If your User model has specific boolean fields
    claims['is_customer'] = getattr(user, 'is_customer', False)
    # Check for 'is_accountant' field, default to False if missing
    claims['is_accountant'] = getattr(user, 'is_accountant', False)
    # Check for 'is_it' or 'is_staff_member'
    claims['is_IT'] = getattr(user, 'is_IT', False)
    # Check for 'is_account_officer
    claims['is_account_officer'] = getattr(user, 'is_account_officer', False)

    # OPTION B: If you use a single 'role' text field (e.g. user.role = 'ADMIN')
    if hasattr(user, 'role'):
        role_name = str(user.role).upper()
        if role_name == 'ACCOUNTANT':
            claims['is_accountant'] = True
        elif role_name == 'IT':
            claims['is_IT'] = True
        elif role_name == 'ACCOUNT OFFICER':
            claims['is_account_officer'] = True
        elif role_name == 'CUSTOMER':
            claims['is_customer'] = True

    return claims

def combine_custom_claims(token):
    """
    The Hook Function: Called by SimpleJWT to finalize the token payload.
    """
    user = token.user
    
    # 1. Start with the default payload (user_id, exp, jti)
    payload = token.payload
    
    # 2. Get your custom data
    custom_data = get_custom_claims(user)
    
    # 3. Merge them into the payload
    payload.update(custom_data)
    
    return payload