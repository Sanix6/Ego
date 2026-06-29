from django.db import models


class BonusType(models.TextChoices):
    ORDERS_COUNT = "orders_count", "За количество заказов"
    ONLINE_HOURS = "online_hours", "За онлайн время"
    PEAK_HOURS = "peak_hours", "Часы пик"
    RATING = "rating", "Высокий рейтинг"
    MISSION = "mission", "Миссия"
    NEWBIE = "newbie", "Новичок"



class WorkerType(models.TextChoices):
    DRIVER = "driver", "Таксист"
    COURIER = "courier", "Курьер"



class PaymentChannel(models.TextChoices):
    CASH = "cash", "Наличка"
    ONLINE = "online", "Онлайн"



class TransactionType(models.TextChoices):
    ORDER_EARNING_CASH = "order_earning_cash", "Доход наличными"
    ORDER_EARNING_ONLINE = "order_earning_online", "Доход онлайн"

    DEPOSIT = "deposit", "Пополнение"

    COMMISSION = "cash_commission", 'Вычет комиссии'

    WITHDRAWAL_HOLD = "withdrawal_hold", "Холд на вывод"
    WITHDRAWAL = "withdrawal", "Вывод"
    WITHDRAWAL_CANCEL = "withdrawal_cancel", "Отмена вывода"

    ADJUSTMENT = "adjustment", "Корректировка"

    BONUS = "bonus", "Бонус"


class TransactionStatus(models.TextChoices):
    PENDING = "pending", "В ожидании"
    COMPLETED = "completed", "Выполнено"
    CANCELED = "canceled", "Отменено"


class WithdrawalStatus(models.TextChoices):
    PENDING = "pending", "В ожидании"
    APPROVED = "approved", "Одобрено"
    REJECTED = "rejected", "Отклонено"
    # PAID = "paid", "Выплачено"
    CANCELED = "canceled", "Отменено"



class PaymentProvider(models.TextChoices):
    MKASSA = "mkassa", "MKassa"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Наличка"
    ONLINE = "online", "Онлайн"



class PaymentStatus(models.TextChoices):
    PENDING = "pending", "В ожидании"
    PAID = "paid", "Оплачено"
    FAILED = "failed", "Ошибка"
    CANCELED = "canceled", "Отменено"