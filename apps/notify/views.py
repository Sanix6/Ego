from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import PushDeviceRegisterSerializer


class PushDeviceRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PushDeviceRegisterSerializer(
            data=request.data,
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        device = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Push устройство зарегистрировано",
                "data": {
                    "device_id": device.id,
                    "onesignal_id": device.onesignal_id,
                },
            },
            status=status.HTTP_200_OK,
        )