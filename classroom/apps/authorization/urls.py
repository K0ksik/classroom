from django.urls import path
from .views import (
    LoginView, logout_view, verify_email, request_verification_code,
    change_password, request_password_reset, reset_password, update_avatar 
)

urlpatterns = [
    path('login/', LoginView.as_view(), name="login"),
    path('logout/', logout_view, name="logout"),
    path('verify-email/', verify_email, name="verify-email"),
    path('request-verification-code/', request_verification_code, name="request-verification-code"),
    
    path('change-password/', change_password, name="change-password"),
    path('request-password-reset/', request_password_reset, name="request-password-reset"),
    path('reset-password/', reset_password, name="reset-password"),

    path('update_avatar/', update_avatar, name="update_avatar"),
]