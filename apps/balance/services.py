import os
import requests
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date, timedelta
from django.utils.timezone import localtime
from .models import OrderPayment, PaymentMethod, PaymentStatus, PaymentProvider


def check_wallet_balance(wallet, amount: Decimal) -> bool:
    return wallet.balance >= amount



from datetime import timedelta
from django.utils.timezone import (
    localtime,
    now,
    is_naive,
    make_aware,
)
from django.utils import timezone


def format_date(dt):
    if not dt:
        return None

    if is_naive(dt):
        dt = make_aware(dt, timezone.get_current_timezone())

    dt = localtime(dt)

    today = localtime(now()).date()
    yesterday = today - timedelta(days=1)

    if dt.date() == today:
        return f"Сегодня {dt.strftime('%H:%M')}"

    elif dt.date() == yesterday:
        return f"Вчера {dt.strftime('%H:%M')}"

    return dt.strftime("%d.%m.%Y %H:%M")