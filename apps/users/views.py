from rest_framework import status, permissions, generics, views
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import login
from .models import User
from rest_framework.authtoken.models import Token
from .serializers import *
from assets.utils import send_sms, send_verification_sms
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import MethodNotAllowed
from drf_spectacular.utils import extend_schema
from django.db import transaction
from services.geo import RedisGeoService
from .models import WorkerLocation, WorkerStatus
from apps.balance.models import WorkerWallet
from apps.taxi.models import TaxiRide
from apps.delivery.models import Delivery
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet




class SendCodeView(generics.GenericAPIView):
    serializer_class = SendCodeSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]

        user, created = User.objects.get_or_create(phone=phone)

        if not user.is_active:
            user.is_active = True
            user.save()

        sms_sent = send_verification_sms(user)

        if not sms_sent:
            return Response(
                {"message": "Не удалось отправить код"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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
    

class DriverRegisterView(generics.GenericAPIView):
    serializer_class = DriverRegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        WorkerWallet.objects.get_or_create(worker=user)

        sms_sent = send_verification_sms(user)

        if not sms_sent:
            return Response(
                {
                    "message": "Пользователь создан, но SMS не отправлено",
                    "phone": user.phone,
                    "user_type": user.user_type,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "message": "Код подтверждения отправлен на телефон",
                "phone": user.phone,
                "user_type": user.user_type,
            },
            status=status.HTTP_200_OK
        )


class VerifyCodeDriverView(generics.GenericAPIView):
    serializer_class = VerifyCodeDriverSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        try:
            user = User.objects.get(phone=phone, user_type="driver")
        except User.DoesNotExist:
            return Response(
                {"message": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.verification_code != code:
            return Response(
                {"message": "Неверный код"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.verification_code = None
        user.save(update_fields=["verification_code"])

        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "message": "Номер успешно подтвержден"
            },
            status=status.HTTP_200_OK
        )

class ResendCodeDriverView(generics.GenericAPIView):
    serializer_class = ResendCodeDriverSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]

        try:
            user = User.objects.get(phone=phone, user_type="driver")
        except User.DoesNotExist:
            return Response(
                {"message": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        send_verification_sms(user)

        return Response(
            {
                "message": "Код отправлен повторно",
                "expires_in": 120
            },
            status=status.HTTP_200_OK
        )



@extend_schema(methods=['PUT'], exclude=True)
class ScanPersonalDriverView(generics.UpdateAPIView):
    serializer_class = ScanPersonalDriverSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user.driver_profile

@extend_schema(methods=['PUT'], exclude=True)
class ScanDriversLicenseView(generics.UpdateAPIView):
    serializer_class = ScanDriversLicenseSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user.driver_profile

@extend_schema(methods=['PUT'], exclude=True)
class ScanDriversAutoView(generics.UpdateAPIView):
    serializer_class = ScanDriversAutoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user.driver_profile


class UserAddressViewSet(ModelViewSet):
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAddress.objects.filter(
            user=self.request.user
        ).order_by("-id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PersonalInfoView(generics.RetrieveAPIView):
    serializer_class = PersonalInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"detail": "Вы вышли из системы"})
        except Exception:
            return Response({"error": "Ошибка выхода"}, status=400)



class DeleteProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save()

        return Response({"detail": "Аккаунт деактивирован"}, status=status.HTTP_200_OK)

class WorkerLocationUpdateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WorkerLocationUpdateSerializer

    def post(self, request, *args, **kwargs):
        user = request.user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            location, _ = WorkerLocation.objects.update_or_create(
                user=user,
                defaults={
                    "lat": data["lat"],
                    "lon": data["lon"],
                }
            )

            worker_status, _ = WorkerStatus.objects.get_or_create(user=user)

            if "is_online" in data:
                worker_status.is_online = data["is_online"]

            worker_status.save()

        if user.user_type in ["driver", "courier"]:
            if worker_status.is_online:
                RedisGeoService.add_worker(
                    user_type=user.user_type,
                    user_id=user.id,
                    lat=location.lat,
                    lon=location.lon,
                )
            else:
                RedisGeoService.remove_worker(
                    user_type=user.user_type,
                    user_id=user.id,
                )

        return Response(
            {
                "success": True,
                "message": "Локация обновлена",
                "data": {
                    "lat": location.lat,
                    "lon": location.lon,
                    "is_online": worker_status.is_online,
                }
            },
            status=status.HTTP_200_OK
        )

class UpdateProfileView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user

        if hasattr(user, "courier_profile"):
            return user.courier_profile, "courier"
        elif hasattr(user, "driver_profile"):
            return user.driver_profile, "driver"

        return None, None

    def get_serializer_class(self):
        user = self.request.user

        if hasattr(user, "courier_profile"):
            return CourierProfileSerializer
        elif hasattr(user, "driver_profile"):
            return DriverProfileSerializer

        return None

    def patch(self, request, *args, **kwargs):
        obj, role = self.get_object()

        if not obj:
            return Response({"detail": "Профиль не найден"}, status=404)

        serializer = self.get_serializer(
            obj,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "type": role,
            "data": serializer.data
        })

class WorkerProfile(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_profile(self, user):
        if hasattr(user, "courier_profile"):
            return user.courier_profile, "courier", CourierProfileSerializer
        elif hasattr(user, "driver_profile"):
            return user.driver_profile, "driver", DriverProfileSerializer
        return None, None, None

    def get(self, request, *args, **kwargs):
        user = request.user
        profile, role, serializer_class = self.get_profile(user)

        if not profile:
            return Response({"detail": "Профиль не найден"}, status=404)

        profile_data = serializer_class(profile).data
        user_data = UserSerializer(user).data

        return Response({
            "type": role,
            "user": user_data,
            "profile": profile_data
        })

class MyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        order_type = request.GET.get("type", "all")
        data = []

        if order_type in ["all", "taxi"]:
            for ride in TaxiRide.objects.filter(client=user, is_hidden_for_client=False):
                data.append({
                    "id": ride.id,
                    "type": "taxi",
                    "status": ride.status,
                    "from_address": ride.point_a,
                    "to_address": ride.point_b,
                    "price": ride.price,
                    "distance_km": ride.distance_km,
                    "duration_min": ride.duration_min,
                    "created_at": ride.requested_at,
                })

        if order_type in ["all", "delivery"]:
            for d in Delivery.objects.filter(client=user, is_hidden_for_client=False):
                data.append({
                    "id": d.id,
                    "type": "delivery",
                    "status": d.delivery_status,
                    "from_address": d.point_a,
                    "to_address": d.point_b,
                    "price": d.price,
                    "distance_km": d.planned_distance_km,
                    "duration_min": d.planned_duration_min,
                    "created_at": d.created_at,
                })

        data.sort(key=lambda x: x["created_at"], reverse=True)

        serializer = MyOrderListSerializer(data, many=True)
        return Response(serializer.data)

class MyOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_type, pk):
        user = request.user

        if order_type == "taxi":
            obj = get_object_or_404(TaxiRide, pk=pk, client=user)
            return Response(TaxiRideDetailSerializer(obj).data)

        elif order_type == "delivery":
            obj = get_object_or_404(Delivery, pk=pk, client=user)
            return Response(DeliveryDetailSerializer(obj).data)

        return Response({"error": "Invalid type"}, status=400)


class MyOrderDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, order_type, pk):
        user = request.user

        if order_type == "taxi":
            obj = get_object_or_404(TaxiRide, pk=pk, client=user)
            obj.is_hidden_for_client = True
            obj.save(update_fields=["is_hidden_for_client"])

        elif order_type == "delivery":
            obj = get_object_or_404(Delivery, pk=pk, client=user)
            obj.is_hidden_for_client = True
            obj.save(update_fields=["is_hidden_for_client"])

        else:
            return Response(
                {"detail": "Invalid type"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoProfileView(generics.GenericAPIView):
    serializer_class = LogoProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)