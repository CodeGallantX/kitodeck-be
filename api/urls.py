from django.urls import path
from .views import (
    sign_up, login_view, logout_view, process_data, get_user_details, 
    analyze_text, scan_image, analyze_message, check_conversation_safety,
    scan_image_for_safety
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Authentication endpoints
    path('auth/signup/', sign_up, name='signup'),
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User profile endpoints
    path('user/details/', get_user_details, name='user_details'),
    
    # Functional endpoints
    path('analyze/text/', analyze_text, name='analyze_text'),
    path('scan/image/', scan_image, name='scan_image'),
    path('process-data/', process_data, name='process_data'),
    
    # Kito protection endpoints
    path('safety/analyze-message/', analyze_message, name='analyze_message'),
    path('safety/check-conversation/', check_conversation_safety, name='check_conversation_safety'),
    path('safety/scan-image/', scan_image_for_safety, name='scan_image_for_safety'),
]