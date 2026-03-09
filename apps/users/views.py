from rest_framework import status, permissions, generics
from rest_framework.response import Response
from django.contrib.auth import login
from .models import User
from rest_framework.authtoken.models import Token
from .serializers import SendCodeSerializer, VerifyCodeSerializer


class SendCodeView(generics.GenericAPIView):
    serializer_class = SendCodeSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        user, _ = User.objects.get_or_create(phone=phone)

        code = user.generate_code()
        return Response(
            {"message": "Verification code sent"},
            status=status.HTTP_200_OK,
        )
    



class VerifyCodeView(generics.GenericAPIView):
    serializer_class = VerifyCodeSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.verification_code != code:
            return Response(
                {"error": "Invalid code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.verification_code = None
        user.save(update_fields=["verification_code"])

        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "user_id": user.id,
                "phone": user.phone,
            },
            status=status.HTTP_200_OK,
        )
    
