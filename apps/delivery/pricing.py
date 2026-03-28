from decimal import Decimal, ROUND_HALF_UP

from apps.delivery.models import DeliveryTariff


class DeliveryPricingError(Exception):
    pass


class DeliveryPricingService:
    @staticmethod
    def calculate_tariff_price(
        *,
        tariff: DeliveryTariff,
        distance_km: Decimal,
        duration_min: int,
    ) -> Decimal:
        distance_km = Decimal(str(distance_km))
        duration_min = int(duration_min)

        included_km = Decimal(str(tariff.included_km))
        included_min = int(tariff.included_min)

        paid_km = max(distance_km - included_km, Decimal("0"))
        paid_min = max(duration_min - included_min, 0)

        total = (
            Decimal(str(tariff.base_fare))
            + paid_km * Decimal(str(tariff.per_km_rate))
            + Decimal(str(paid_min)) * Decimal(str(tariff.per_min_rate))
        )

        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_commission(*, price: Decimal, commission_percent: Decimal) -> tuple[Decimal, Decimal]:
        price = Decimal(str(price))
        commission_percent = Decimal(str(commission_percent))

        commission_amount = (
            price * commission_percent / Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        courier_payout = (
            price - commission_amount
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return commission_amount, courier_payout

    @classmethod
    def get_prices_for_all_types(cls, *, distance_km: Decimal, duration_min: int) -> list[dict]:
        tariffs = DeliveryTariff.objects.filter(is_active=True).order_by("id")

        if not tariffs.exists():
            raise DeliveryPricingError("Активные тарифы доставки не найдены.")

        results = []

        for tariff in tariffs:
            price = cls.calculate_tariff_price(
                tariff=tariff,
                distance_km=distance_km,
                duration_min=duration_min,
            )

            commission_amount, courier_payout = cls.calculate_commission(
                price=price,
                commission_percent=tariff.commission_percent,
            )

            results.append({
                "type_delivery": tariff.type_delivery,
                "label": tariff.get_type_delivery_display(),
                "price": str(price),
                "estimated_price": str(price),
                "total_price": str(price),
                "commission_amount": str(commission_amount),
                "courier_payout": str(courier_payout),
            })

        return results