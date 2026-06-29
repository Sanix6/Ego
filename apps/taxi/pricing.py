from decimal import Decimal, ROUND_HALF_UP

from apps.main.models import Tariff
from apps.main.models import TaxiCommission


class PricingError(Exception):
    pass


class PricingService:

    @staticmethod
    def calculate_tariff_price(
        *,
        tariff: Tariff,
        distance_km: Decimal,
        duration_min: int
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

    # =========================
    # FIXED COMMISSION LOGIC
    # =========================
    @staticmethod
    def calculate_commission(*, price: Decimal, car_class: str, payment_method: str) -> tuple[Decimal, Decimal]:

        price = Decimal(str(price))

        commission_rule = TaxiCommission.objects.filter(
            car_class=car_class,
            payment_method=payment_method,
            is_active=True
        ).first()

        if not commission_rule:
            commission_rule = TaxiCommission.objects.filter(
                car_class=car_class,
                payment_method__isnull=True,
                is_active=True
            ).first()

        if not commission_rule:
            raise PricingError("Комиссия для тарифа не найдена.")

        commission_amount = (
            price * commission_rule.commission_percent / Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if commission_amount < commission_rule.min_commission:
            commission_amount = commission_rule.min_commission

        if commission_rule.max_commission and commission_amount > commission_rule.max_commission:
            commission_amount = commission_rule.max_commission

        driver_payout = (
            price - commission_amount
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return commission_amount, driver_payout

    @staticmethod
    def get_active_tariff(*, car_class: str) -> Tariff:
        try:
            return Tariff.objects.get(car_class=car_class, is_active=True)
        except Tariff.DoesNotExist as exc:
            raise PricingError(
                f"Активный тариф для class={car_class} не найден."
            ) from exc

    @classmethod
    def get_price_details_for_tariff(
        cls,
        *,
        car_class: str,
        distance_km: Decimal,
        duration_min: int,
        payment_method: str = "cash"
    ) -> dict:

        tariff = cls.get_active_tariff(car_class=car_class)

        price = cls.calculate_tariff_price(
            tariff=tariff,
            distance_km=distance_km,
            duration_min=duration_min,
        )

        commission_amount, driver_payout = cls.calculate_commission(
            price=price,
            car_class=car_class,
            payment_method=payment_method,
        )

        return {
            "tariff": tariff,
            "distance_km": Decimal(str(distance_km)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "duration_min": int(duration_min),
            "price": price,
            "estimated_price": price,
            "total_price": price,
            "commission_amount": commission_amount,
            "driver_payout": driver_payout,
        }

    @classmethod
    def get_prices_for_city(cls, *, distance_km: Decimal, duration_min: int) -> list[dict]:

        tariffs = Tariff.objects.filter(is_active=True).order_by("id")

        if not tariffs.exists():
            raise PricingError("Активные тарифы не найдены.")

        results = []

        for tariff in tariffs:

            price = cls.calculate_tariff_price(
                tariff=tariff,
                distance_km=distance_km,
                duration_min=duration_min,
            )

            results.append({
                "car_class": tariff.car_class,
                "label": tariff.get_car_class_display(),
                "price": str(price),
            })

        return results