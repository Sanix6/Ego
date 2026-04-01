from django.db import models


class WorkerType(models.TextChoices):
    DRIVER = "driver", "Таксист"
    COURIER = "courier", "Курьер"


class PaymentChannel(models.TextChoices):
    CASH = "cash", "Наличка"
    MBANK = "mbank", "MBank"


class TransactionType(models.TextChoices):
    ORDER_EARNING = "order_earning", "Доход по заказу"
    WITHDRAWAL_HOLD = "withdrawal_hold", "Холд на вывод"
    WITHDRAWAL = "withdrawal", "Вывод"
    WITHDRAWAL_CANCEL = "withdrawal_cancel", "Отмена вывода"
    ADJUSTMENT = "adjustment", "Корректировка"


class TransactionStatus(models.TextChoices):
    PENDING = "pending", "В ожидании"
    COMPLETED = "completed", "Выполнено"
    CANCELED = "canceled", "Отменено"


class WithdrawalStatus(models.TextChoices):
    PENDING = "pending", "В ожидании"
    APPROVED = "approved", "Подтверждено"
    REJECTED = "rejected", "Отклонено"
    PAID = "paid", "Выплачено"
    CANCELED = "canceled", "Отменено"



class PaymentProvider(models.TextChoices):
    MKASSA = "mkassa", "MKassa"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Наличка"
    MBANK = "mbank", "MBank"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "В ожидании"
    PAID = "paid", "Оплачено"
    FAILED = "failed", "Ошибка"
    CANCELED = "canceled", "Отменено"