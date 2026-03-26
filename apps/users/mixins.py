from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now

class DispatchAdminMixin:
    list_per_page = 25

    readonly_fields = (
        "map_preview",
        "last_seen_view",
        "location_updated_view",
    )

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or "-"
    full_name.short_description = "ФИО"

    def colored_online(self, obj):
        status = getattr(obj, "worker_status", None)
        is_online = getattr(status, "is_online", False)
        color = "green" if is_online else "red"
        text = "ONLINE" if is_online else "OFFLINE"
        return format_html('<b style="color:{}">{}</b>', color, text)
    colored_online.short_description = "Статус"

    def colored_busy(self, obj):
        status = getattr(obj, "worker_status", None)
        is_busy = getattr(status, "is_busy", False)
        color = "orange" if is_busy else "green"
        text = "BUSY" if is_busy else "FREE"
        return format_html('<b style="color:{}">{}</b>', color, text)
    colored_busy.short_description = "Занятость"

    def last_seen_colored(self, obj):
        status = getattr(obj, "worker_status", None)
        if not status or not status.last_seen:
            return "-"

        delta = now() - status.last_seen
        if delta.total_seconds() < 60:
            color = "green"
        elif delta.total_seconds() < 300:
            color = "orange"
        else:
            color = "red"

        return format_html(
            '<span style="color:{}">{}</span>',
            color,
            status.last_seen.strftime("%Y-%m-%d %H:%M:%S")
        )
    last_seen_colored.short_description = "Последняя активность"

    def last_seen_view(self, obj):
        return self.last_seen_colored(obj)
    last_seen_view.short_description = "Последняя активность"

    def lat(self, obj):
        location = getattr(obj, "worker_location", None)
        return location.lat if location else "-"
    lat.short_description = "Lat"

    def lon(self, obj):
        location = getattr(obj, "worker_location", None)
        return location.lon if location else "-"
    lon.short_description = "Lon"

    def map_link(self, obj):
        location = getattr(obj, "worker_location", None)
        if not location:
            return "-"
        url = f"https://www.google.com/maps?q={location.lat},{location.lon}"
        return format_html('<a href="{}" target="_blank">📍 Открыть карту</a>', url)
    map_link.short_description = "Карта"

    def map_preview(self, obj):
        return self.map_link(obj)
    map_preview.short_description = "Карта"

    def location_updated_at_colored(self, obj):
        location = getattr(obj, "worker_location", None)
        if not location or not location.updated_at:
            return "-"

        delta = now() - location.updated_at
        if delta.total_seconds() < 60:
            color = "green"
        elif delta.total_seconds() < 300:
            color = "orange"
        else:
            color = "red"

        return format_html(
            '<span style="color:{}">{}</span>',
            color,
            location.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        )
    location_updated_at_colored.short_description = "Гео обновлено"

    def location_updated_view(self, obj):
        return self.location_updated_at_colored(obj)
    location_updated_view.short_description = "Гео обновлено"

