from rest_framework import serializers
from ..models import *

class LoginSerializer(serializers.Serializer):
    
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = user
        fields = ['username', 'password',]
        
    def login(self, validated_data):
        password = validated_data.pop('password')

        
        
class CustomerIdentitySerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = user
        fields = ['username','first_name', 'last_name', 'email', 'phone',
                  'sex', 'password']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        
        # Create the user instance
        user_instance = user.objects.create(**validated_data)

        # Set the hashed password
        user_instance.set_password(password)
        user_instance.save()

        return user_instance



class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = user
        fields = ['phone', 'email']
        
class UserDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = user
        fields = ['username']

