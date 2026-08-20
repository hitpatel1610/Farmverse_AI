from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from authentication.services.otp_service import OTPService
from authentication.services.email_service import EmailService
from authentication.services.jwt_service import JWTService
from django.contrib.auth.hashers import check_password

User = get_user_model()


class AuthService:
    """
    Facade service coordinating authentication operations, business logic rules,
    and credentials verification.
    """
    @staticmethod
    def register_user(validated_data: dict) -> "User":
        """
        Validate uniqueness, hash password, generate verification OTP, and save user.
        """
        mobile = validated_data.get('mobile')
        email = validated_data.get('email')
        
        # Check duplicate mobile
        if User.objects.filter(mobile=mobile).exists():
            raise ValidationError({'mobile': 'This mobile number is already registered.'})
            
        # Check duplicate email
        if User.objects.filter(email=email).exists():
            raise ValidationError({'email': 'This email address is already registered.'})
            
        # Create user (User model set_password hashes it automatically)
        user = User.objects.create_user(
            mobile=mobile,
            email=email,
            full_name=validated_data.get('full_name'),
            role=validated_data.get('role', 'Farmer'),
            password=validated_data.get('password'),
        )
        
        # Generate registration verification OTP
        otp_code = OTPService.generate_otp(mobile)
        
        # Send OTP email
        #EmailService.send_otp_email(user.email, otp_code)
        
        return user

    @staticmethod
    def authenticate_user(credential: str, password_raw: str, role_scope: str) -> dict:
        """
        Look up user by mobile OR email, check password, verify active/role status,
        and generate JWT tokens.
        """
        # Try finding by mobile first, then email
        user = None
        if credential.isdigit() or len(credential) <= 15:
            user = User.objects.filter(mobile=credential).first()
        
        if not user:
            user = User.objects.filter(email=credential).first()
            
        if not user:
            raise AuthenticationFailed("Invalid mobile number or email credentials.")
            
        # Check password
        if not user.check_password(password_raw):
            raise AuthenticationFailed("Incorrect password code.")
            
        # Validate role matches requested login portal
        if user.role != role_scope:
            raise AuthenticationFailed(f"Unauthorized. You do not have permissions to access the {role_scope} portal.")
            
        # Validate active status
        if not user.is_active:
            raise AuthenticationFailed("Your account is disabled. Please contact administrator.")

            
        # Automatically verify account on initial login if it's the first time
        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=['is_verified'])

        # Generate JWT tokens
        tokens = JWTService.generate_tokens_for_user(user)
        
        return {
            'tokens': tokens,
            'user': {
                'uuid': str(user.uuid),
                'full_name': user.full_name,
                'mobile': user.mobile,
                'email': user.email,
                'role': user.role,
                'is_verified': user.is_verified
            }
        }

    @staticmethod
    def request_forgot_password(mobile: str) -> bool:
        """
        Check if user exists with mobile, generate OTP, send OTP code via email.
        """
        user = User.objects.filter(mobile=mobile).first()
        if not user:
            raise ValidationError("No registered user found with this mobile number.")
            
        # Generate OTP
        otp_code = OTPService.generate_otp(mobile)
        
        # Dispatch to email
        sent = EmailService.send_otp_email(user.email, otp_code)
        
        return sent

    @staticmethod
    def verify_forgot_password_otp(mobile: str, otp_code: str) -> bool:
        """
        Validate the recovery OTP.
        """
        # Verify otp
        is_valid = OTPService.verify_otp(mobile, otp_code)
        if not is_valid:
            raise ValidationError("Invalid or expired OTP code.")
        return True

    @staticmethod
    def reset_password(mobile: str, new_password_raw: str) -> bool:
        """
        Reset user's password to the new hash.
        """
        user = User.objects.filter(mobile=mobile).first()
        if not user:
            raise ValidationError("User not found.")
            
        user.set_password(new_password_raw)
        user.save(update_fields=['password'])
        return True

    @staticmethod
    def update_profile(user, validated_data: dict) -> "User":
        """
        Update user profile information.
        """
        full_name = validated_data.get('full_name')
        email = validated_data.get('email')
        
        # Check duplicate email if it changes
        if email and email != user.email:
            if User.objects.filter(email=email).exists():
                raise ValidationError({'email': 'This email address is already taken.'})
            user.email = email
            
        if full_name:
            user.full_name = full_name
            
        user.save()
        return user
