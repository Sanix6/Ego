PLATFORM_CHOICES = (
        ("android", "Android"),
        ("ios", "iOS"),
        ("web", "Web"),
    )


STATUS_CHOICES = (
        ("pending", "Ожидает"),
        ("sent", "Отправлено"),
        ("failed", "Ошибка"),
        ("canceled", "Отменено"),
    )

EVENT_TYPES = (
        ("slot_remind_1h", "За 1 час до начала слота"),
        ("slot_started", "Слот начался"),
        ("slot_finished", "Слот завершен"),

        ("delivery_offer_new", "Курьеру пришел заказ"),
        ("delivery_courier_arrived", "Курьер прибыл"),
        ("delivery_started", "Доставка началась"),
        ("delivery_completed", "Доставка завершена"),

        ("taxi_offer_new", "Водителю пришел заказ"),
        ("taxi_driver_arrived", "Водитель прибыл"),
        ("taxi_started", "Поездка началась"),
        ("taxi_completed", "Поездка завершена"),
    )