from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


app_name = 'Identity_service_api'


urlpatterns = [
    
    path('token/', TokenObtainPairView.as_view(), name='token'),        #Good
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),       #Good
    path('customer_register/', views.CustomerRegisterView.as_view(), name='customer_register'),
    path('staff_register/', views.StaffRegisterView.as_view(), name='staff_register'),
    path('login/', views.LoginView.as_view(), name='login'),  #Good
    path('logout/', views.LogoutView.as_view(), name='logout'),                        #Good
    path('user_details/', views.UserDetailView.as_view(), name='user_details'),

]