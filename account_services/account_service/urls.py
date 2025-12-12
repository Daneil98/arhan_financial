from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = 'account_service'

urlpatterns = [
    
#    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),        #Good
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),       #Good

]