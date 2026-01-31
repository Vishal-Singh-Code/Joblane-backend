from rest_framework.throttling import AnonRateThrottle


class RegisterThrottle(AnonRateThrottle):
    scope = "register"

class VerifyOtpThrottle(AnonRateThrottle):
    scope = "verify_otp"

class SendOtpThrottle(AnonRateThrottle):
    scope = "send_otp"

class ForgetPasswordThrottle(AnonRateThrottle):
    scope = "forgot_password"

class VerifyForgetOtpThrottle(AnonRateThrottle):
    scope = "verify_forgot_otp"

class ResetPasswordThrottle(AnonRateThrottle):
    scope = "reset_password"

class LoginThrottle(AnonRateThrottle):
    scope = "login"

class GoogleLoginThrottle(AnonRateThrottle):
    scope = "google_login"