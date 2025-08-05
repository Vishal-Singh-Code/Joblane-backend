from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView, RegisterView, GoogleLoginView, ProfileAPIView,LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('google/', GoogleLoginView.as_view(), name='google_login'),
    path('profile/', ProfileAPIView.as_view(), name='user-profile'),
    path('logout/', LogoutView.as_view(), name='logout'),

]

