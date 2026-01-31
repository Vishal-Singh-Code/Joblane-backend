from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, SendOtpView, VerifyOtpView, CustomTokenObtainPairView, GoogleLoginView, ProfileAPIView, LogoutView, ForgotPasswordView, VerifyForgotOtpView, ResetPasswordView

urlpatterns = [
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    path('register/', RegisterView.as_view(), name='register'),
    path("send-otp/", SendOtpView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOtpView.as_view(), name="verify-otp"),

    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('google/', GoogleLoginView.as_view(), name='google-login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('profile/', ProfileAPIView.as_view(), name='user-profile'),

    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("forgot-password/verify-otp/", VerifyForgotOtpView.as_view(), name="verify-forgot-otp"),
    path("forgot-password/reset/", ResetPasswordView.as_view(), name="reset-password"),

]

