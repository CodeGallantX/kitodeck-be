from django.urls import path
from .views import sign_up, login_view, process_data
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('signup/', sign_up, name='signup'),
    path('login/', login_view, name='login'),
    path('process-data/', process_data, name='process_data'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
