from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.schemas import AutoSchema
from rest_framework.compat import coreapi, coreschema, uritemplate

class SignupView(APIView):
    permission_classes = (AllowAny,)
    schema = AutoSchema(manual_fields=[
        coreapi.Field(
            "email",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "password",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "first_name",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "last_name",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "gender",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "dob",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "phone_no",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "address",
            required=True,
            location="form",
            schema=coreschema.String()
        )
    ])
    def post(self, request, format=None):
        """
        Create User/ Signup User
        """
        result = userService.sign_up(request, format=None)
        return Response(result, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = (AllowAny,)
    schema = AutoSchema(manual_fields=[
        coreapi.Field(
            "email",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "password",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "device_id",
            required=False,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "device-type",
            required=False,
            location="header",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "app-version",
            required=False,
            location="header",
            schema=coreschema.String()
        )
    ])

    def post(self, request, format=None):
        """
        Login
        """
        result = userService.login(request, format=None)
        return Response(result, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Logout
    """
    schema = AutoSchema(manual_fields=[

        coreapi.Field(
            "device-type",
            required=False,
            location="header",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "device_id",
            required=False,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "app-version",
            required=False,
            location="header",
            schema=coreschema.String()
        )

    ])

    def post(self, request, format=None):
        # simply delete the token to force a login
        result = userService.logout(request, format=None)
        return Response(result, status=status.HTTP_200_OK)

class SendOTPView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, email, format=None):
        """
        Send OTP
        """
        result = userService.generate_otp(request, email, format=None)
        return Response(result, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = (AllowAny,)
    schema = AutoSchema(manual_fields=[
        coreapi.Field(
            "email",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "otp",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
    ])

    def post(self, request, format=None):
        """
        Verify OTP
        """
        result = userService.verify_otp(request, format=None)
        return Response(result, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    permission_classes = (AllowAny,)

    schema = AutoSchema(manual_fields=[
        coreapi.Field(
            "email",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "password",
            required=True,
            location="form",
            schema=coreschema.String()
        ),
    ])

    def put(self, request, format=None):
        """
        Reset Password
        """
        result = userService.reset_password(request, format=None)
        return Response(result, status=status.HTTP_200_OK)
