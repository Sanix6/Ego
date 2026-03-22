ORDER_STATUSES = [
    ("created", "CTE"),
    ("processing", "Ожидание выдачи"),
    ("ready", "Pick Up"),
    ("shipped", "Курьер в пути"),
]

DELIVERY_STATUSES = (
    ("searching_courier", "Поиск курьера"),
    ("courier_assigned", "Курьер назначен"),
    ("courier_arrived", "Курьер прибыл"),
    ("picked_up", "Забрал посылку"),
    ("in_delivery", "В пути"),
    ("delivered", "Доставлено"),
    ("canceled", "Отменено"),
    ("courier_arrived_b", "Курьер прибыл в точку назначения"),
    ("waiting_pickup", "Бесплатное ожидание"),
)


DELIVERY_TYPES = [
    ("express", "Экспресс"),
    ("standard", "Стандарт"),
]

USER_TYPERS = [
    ("client", "Клиент"),
    ("courier", "Курьер"),
    ("driver", "Водитель"),
    ("admin", "Администратор"),
    ("operator", "Оператор"),
]

ORDER_TYPES = [
    ("express", "Экспресс"),
    ("standard", "Стандарт"),
]


OFFER_STATUSES = (
        ("pending", "Ожидает ответа"),
        ("accepted", "Принят"),
        ("rejected", "Отклонен"),
        ("expired", "Истек"),
    )




#######Такси choices.py#######
TAXI_STATUSES = (
    ("pending", "В ожидании"),
    ("assigned", "Назначен водитель"),
    ("accepted", "Водитель принял"),
    ("arrived", "Водитель приехал"),
    ("in_trip", "В поездке"),
    ("completed", "Завершено"),
    ("canceled", "Отменено"),
    ("failed", "Не удалось"),
)

CAR_CLASSES = (
    ("econom", "Эконом"),
    ("comfort", "Комфорт"),
    ("business", "Бизнес"),
    ("van", "Минивэн"),
)

PAYMENT_METHODS = (
    ("cash", "Наличные"),
    ("card", "Карта"),
)

PAYMENT_STATUSES = (
    ("unpaid", "Не оплачено"),
    ("paid", "Оплачено"),
    ("refunded", "Возврат"),
)


STATUS_CHOICES = (
        ('pending', 'На проверке'),
        ('approved', 'Одобрен'),
        ('rejected', 'Отклонён'),
    )

#Слоты

SLOT_STATUSES = [
    ("in_work", "в работе"),
    ("offered", "предложен"),
    ("planned", "запланирован"),
    ("no_show", "невыход"),
    ("completed", "завершён"),
]


TRANSPORT_TYPES = (
        ("foot", "Пеший"),
        ("bike", "Велосипед"),
        ("moped", "Мопед"),
        ("car", "Машина"),
    )