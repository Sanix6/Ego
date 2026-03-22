from django.contrib import admin
from django.urls import path, include
from .spectacular import urlpatterns as spectacular_urls

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("apps.users.urls")),
    path("api/maps/", include("apps.maps.urls")),
    path("api/delivery/", include("apps.delivery.urls")),
    path("api/taxi/", include("apps.taxi.urls")),
    
] + spectacular_urls

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
