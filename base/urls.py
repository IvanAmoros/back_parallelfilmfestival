from django.urls import path
from .views import (
    ValidateTokenView,
    MyTokenObtainPairView,
    UserRegistrationAPIView,
    PasswordResetView,
    PasswordResetConfirmView,
)
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [

    path('api/password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

	path('api/register/', UserRegistrationAPIView.as_view(), name='register'),
	path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
	path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
	path('api/validate_token/', ValidateTokenView.as_view(), name='validate_token'),
]
