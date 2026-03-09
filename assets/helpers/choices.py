ORDER_STATUSES = [
    ("created", "CTE"),
    ("processing", "Ожидание выдачи"),
    ("ready", "Pick Up"),
    ("shipped", "Курьер в пути"),
]

DELIVERY_STATUSES = [
    ("pending", "Ожидание курьера"),
    ("assigned", "Назначен курьер"),
    ("picked_up", "Заказ забран"),
    ("delivered", "Доставлено"),
    ("canceled", "Отменено"),
]
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


#Слоты

SLOT_STATUSES = [
    ("in_work", "в работе"),
    ("offered", "предложен"),
    ("planned", "запланирован"),
    ("closed_early", "закрыт досрочно"),
    ("paid_break", "оплачиваемая пауза"),
    ("unpaid_break", "неоплачиваемая пауза"),
    ("no_show", "невыход"),
]
