from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import *
from ..tasks import *
from django.contrib.auth import authenticate, login
from django.db.models import Q
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from .serializers import *
from django.db import transaction


#ACCOUNT IDENTITY API VIEWS
"""

class CustomerRegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Use the correct Serializer class name
        serializer = CustomerIdentitySerializer(data=request.data)
        
        # 1. Validate
        serializer.is_valid(raise_exception=True)

        # 2. Save (Calls serializer.create() internally with validated_data)
        # ⚠️ IMPORTANT: This returns the 'CustomerIdentity' profile instance, NOT the User!
        customer_profile = serializer.save()
        
        # 3. Get the actual User object from the relationship
        user = customer_profile.user

        # 4. Prepare data for Celery
        # We access attributes from 'user', not 'customer_profile'
        user_data = {
            'username': str(user.username),
            'id': str(user.id),
            'email': str(user.email),
            'first_name': str(user.first_name),
            'last_name': str(user.last_name),
            # You can also include profile data if needed
            'phone': str(customer_profile.phone)
        }

        # 5. Trigger Async Task
        # Use .delay() or .apply_async()
        publish_customer_created.apply_async(args=[user_data])
        
        return Response({
            'status': 'success', 
            'message': 'Account created successfully',
            'user_id': user.id 
        }, status=status.HTTP_201_CREATED)
"""


class CustomerRegisterView(APIView):
    permission_classes = [AllowAny]  # Allow unrestricted access
    queryset = user.objects.all()
    
    def post(self, request):
        serializer = CustomerIdentitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Validate the data

        # Check if email exists in username or email fields
        if user.objects.filter(username=serializer.validated_data['username']).exists():
            serializer.add_error('message', 'This username is already taken')
            return Response({'status': 'failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
        if user.objects.filter(email=serializer.validated_data['email']).exists():
            serializer.add_error('message', 'This email is already taken')
            return Response({'status': 'failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save the user (handled by the serializer)
        user_info = serializer.create(serializer.validated_data)
 
        user_data = {
            'username': str(user_info.username),
            "id": str(user_info.id),
            "email": str(user_info.email)
        }
        # Create a profile for the user
        #user.objects.create(user=user)
        publish_customer_created.apply_async(args=[user_data])
        
        return Response({'status': 'success', 'message': 'Account created successfully'}, status=status.HTTP_201_CREATED)



class StaffRegisterView(APIView):
    permission_classes = [AllowAny]  # Allow unrestricted access
    queryset = user.objects.all()
    
    def post(self, request):
        serializer = CustomerIdentitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Validate the data

        # Check if email exists in username or email fields
        if user.objects.filter(username=serializer.validated_data['username']).exists():
            serializer.add_error('message', 'This username is already taken')
            return Response({'status': 'failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
        if user.objects.filter(email=serializer.validated_data['email']).exists():
            serializer.add_error('message', 'This email is already taken')
            return Response({'status': 'failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save the user (handled by the serializer)
        user_info = serializer.create(serializer.validated_data)
 
        user_data = {
            'username': str(user_info.username),
            "id": str(user_info.id),
            "email": str(user_info.email)
        }
        # Create a profile for the user
        #user.objects.create(user=user)
        publish_staff_created.apply_async(args=[user_data])
        
        return Response({'status': 'success', 'message': 'Account created successfully'}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]  # Allow unrestricted access
    queryset = user.objects.all()  
    serializer_class = LoginSerializer


    def post(self, request):
        # Parse the username and password from the request
        username = request.data.get('username')
        password = request.data.get('password')

        # Validate the input data using the serializer
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # This raises errors if data is invalid
        
        # Authenticate the user
        User = authenticate(request, username=username, password=password)
        if User is not None:
            if User.is_active:
                # Log the user in (creates a session)
                login(request, User)
                refresh = RefreshToken.for_user(User)
                access_token = str(refresh.access_token)
                user_ = get_object_or_404(user, username=username)
                user_data = {
                    'username': str(user_.username),
                    "user_id": str(user_.id),
                }
                #publish_user_loggedIn.apply_async(args=[user_data])
                return Response({'status': 'success', 'message': 'Logged in successfully', "access_token": access_token, "refresh_token": str(refresh)}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'failed', 'message': 'User account is inactive'}, status=status.HTTP_403_FORBIDDEN)
        else:
            raise AuthenticationFailed("Invalid username or password")
        

class LogoutView(APIView):
    # Standard practice: POST for logout
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({"message": "Logout successful"}, status=200)
            
            return Response({"error": "No refresh token provided"}, status=400)
            
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        

class UserDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    queryset = user.objects.all()
    serializer_class = UserDetailSerializer

    def post(self, request, format=None):
        serializer =UserDetailSerializer(data=request.data)
        if serializer.is_valid():
            User = user.objects.filter(username=serializer.validated_data['username']).first()
            user_data = {
                'username': str(User.username),
                "id": str(User.id),
                "email": str(User.email),
                "first_name": str(User.first_name),
                "last_name": str(User.last_name),
                "phone": str(User.phone),
                "sex": str(User.sex),
                "is_customer": str(User.is_customer),
            }
            
            return Response({"status": "success", "message": user_data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
