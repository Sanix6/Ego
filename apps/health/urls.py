from django.urls import path
from .views import operations_health_dashboard

urlpatterns = [
    path(
        "admin/health/",
        operations_health_dashboard,
        name="operations-health"
    ),
]