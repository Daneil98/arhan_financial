from rest_framework.permissions import BasePermission

class IsAccountant(BasePermission):
    """
    Allows access only if the JWT token has 'is_accountant' set to True.
    """
    def has_permission(self, request, view):
        # 1. Check if user is authenticated at all
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Check the JWT Payload (request.auth)
        # In SimpleJWT, request.auth is the decoded dictionary of the token.
        # This works perfectly across microservices without needing a DB lookup.
        token_payload = request.auth
        
        # Guard against cases where Auth is not JWT (e.g. Session)
        if isinstance(token_payload, dict):
            return token_payload.get('is_accountant', False)
            
        return False
    
class IsAccountOfficer(BasePermission):
    """
    Allows access only if the JWT token has 'is_accountant' set to True.
    """
    def has_permission(self, request, view):
        # 1. Check if user is authenticated at all
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Check the JWT Payload (request.auth)
        # In SimpleJWT, request.auth is the decoded dictionary of the token.
        # This works perfectly across microservices without needing a DB lookup.
        token_payload = request.auth
        
        # Guard against cases where Auth is not JWT (e.g. Session)
        if isinstance(token_payload, dict):
            return token_payload.get('is_account_officer', False)
            
        return False

class IsIT(BasePermission):
    """
    Allows access only if the JWT token has 'is_accountant' set to True.
    """
    def has_permission(self, request, view):
        # 1. Check if user is authenticated at all
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Check the JWT Payload (request.auth)
        # In SimpleJWT, request.auth is the decoded dictionary of the token.
        # This works perfectly across microservices without needing a DB lookup.
        token_payload = request.auth
        
        # Guard against cases where Auth is not JWT (e.g. Session)
        if isinstance(token_payload, dict):
            return token_payload.get('is_IT', False)
            
        return False