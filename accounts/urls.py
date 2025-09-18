from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, SendOtpView, VerifyOtpView, CustomTokenObtainPairView, GoogleLoginView, ProfileAPIView, LogoutView, ForgotPasswordView, VerifyForgotOtpView, ResendForgotOtpView, ResetPasswordView

urlpatterns = [
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('register/', RegisterView.as_view(), name='register'),
    path("send-otp/", SendOtpView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOtpView.as_view(), name="verify-otp"),

    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('google/', GoogleLoginView.as_view(), name='google_login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('profile/', ProfileAPIView.as_view(), name='user-profile'),

    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("forgot-password/verify-otp/", VerifyForgotOtpView.as_view(), name="forgot-verify-otp"),
    path("forgot-password/resend-otp/", ResendForgotOtpView.as_view(), name="forgot-resend-otp"),
    path("forgot-password/reset/", ResetPasswordView.as_view(), name="forgot-reset-password"),

]

