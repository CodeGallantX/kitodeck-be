from django.urls import path
from .views import sign_up, login_view, process_data, get_user_details
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/signup/', sign_up, name='signup'),
    path('auth/login/', login_view, name='login'),
    path('process-data/', process_data, name='process_data'),
    path('user/details/', get_user_details, name='user_details'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]