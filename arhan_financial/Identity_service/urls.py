from django.urls import path, include
from . import views


app_name = 'Identity_service'


urlpatterns = [
    
#    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),        #Good
    path('customer_login/', views.customer_login, name='customer_login'),       #Good
]