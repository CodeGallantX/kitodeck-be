from django.urls import path
from .views import SignUpView, LoginView, LogoutView, ImageScanView, ChatScanView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/details/', UserProfileView.as_view(), name='user-profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('image-scan/', ImageScanView.as_view(), name='image-scan'),
    path('chat-scan/', ChatScanView.as_view(), name='chat-scan'),
]