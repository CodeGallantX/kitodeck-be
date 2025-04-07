from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    sign_up, login_view, logout_view,
    get_user_details, analyze_text, scan_image
)

urlpatterns = [
    # Authentication
    path('auth/signup/', sign_up, name='signup'),
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User
    path('user/', get_user_details, name='user_details'),
    
    # Analysis
    path('analyze/text/', analyze_text, name='analyze_text'),
    path('analyze/image/', scan_image, name='scan_image'),
]