from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Count
from apps.notify.bonus import (
    bonus_reward_created,
    mission_completed,
    bonus_rule_completed,
)

from apps.balance.models import (
    BonusRule,
    BonusMission,
    BonusReward,
    WorkerMissionProgress,
    WorkerWallet,
    WalletTransaction,
)

from apps.balance.choices import (
    TransactionType,
    TransactionStatus,
)




def process_worker_bonuses(worker, event="order_completed", context=None):
    if not worker:
        return

    process_bonus_rules(worker)
    process_bonus_missions(worker)


def process_bonus_rules(worker):
    now = timezone.now()

    rules = BonusRule.objects.filter(
        is_active=True,
    ).filter(
        starts_at__lte=now,
        ends_at__gte=now,
    )

    for rule in rules:

        if not check_rule_matches(worker, rule):
            continue

        if already_rewarded_rule(worker, rule):
            continue

        issue_bonus_reward(
            worker=worker,
            amount=rule.reward_amount,
            bonus_type=rule.bonus_type,
            description=rule.title,
            rule=rule,
        )

def check_rule_matches(worker, rule):

    if rule.required_orders:
        if worker.orders_count < rule.required_orders:
            return False

    if rule.required_rating:
        if worker.rating_avg < rule.required_rating:
            return False

    if rule.required_reviews_count:
        if worker.rating_count < rule.required_reviews_count:
            return False

    if rule.required_online_hours:

        status = getattr(worker, "worker_status", None)

        if not status:
            return False

        online_seconds = status.today_online_seconds

        if status.is_online and status.online_started_at:
            online_seconds += int(
                (
                    timezone.now() - status.online_started_at
                ).total_seconds()
            )

        required_seconds = (
            rule.required_online_hours * 3600
        )

        if online_seconds < required_seconds:
            return False

    return True

def already_rewarded_rule(worker, rule):
    return BonusReward.objects.filter(
        worker=worker,
        rule=rule,
        is_canceled=False,
    ).exists()

def process_bonus_missions(worker):
    now = timezone.now()

    missions = BonusMission.objects.filter(
        is_active=True,
        starts_at__lte=now,
        ends_at__gte=now,
    )

    for mission in missions:

        progress, _ = WorkerMissionProgress.objects.get_or_create(
            worker=worker,
            mission=mission,
        )

        if progress.rewarded:
            continue

        progress.completed_orders += 1

        if progress.completed_orders >= mission.required_orders:
            progress.is_completed = True

        progress.save(
            update_fields=[
                "completed_orders",
                "is_completed",
            ]
        )

        if progress.is_completed and not progress.rewarded:

            issue_bonus_reward(
                worker=worker,
                amount=mission.reward_amount,
                bonus_type="mission",
                description=f"Миссия: {mission.title}",
                mission=mission,
            )

            progress.rewarded = True
            progress.rewarded_at = now

            progress.save(
                update_fields=[
                    "rewarded",
                    "rewarded_at",
                ]
            )
@transaction.atomic
def issue_bonus_reward(
    worker,
    amount,
    bonus_type,
    description,
    mission=None,
    rule=None,
):

    wallet, _ = WorkerWallet.objects.get_or_create(
        worker=worker
    )

    reward = BonusReward.objects.create(
        worker=worker,
        bonus_type=bonus_type,
        rule=rule,
        mission=mission,
        amount=amount,
        description=description,
    )

    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type=TransactionType.BONUS,
        status=TransactionStatus.COMPLETED,
        amount=amount,
        sign=1,
        comment=description,
    )

    bonus_reward_created(reward)

    if mission:
        progress = WorkerMissionProgress.objects.filter(
            worker=worker,
            mission=mission,
        ).first()

        if progress:
            mission_completed(progress)

    if rule:
        bonus_rule_completed(
            worker=worker,
            rule=rule,
            amount=amount,
        )

    return reward

def process_first_order_bonus(worker):
    if worker.orders_count != 1:
        return

    exists = BonusReward.objects.filter(
        worker=worker,
        description="Бонус за первый заказ",
    ).exists()

    if exists:
        return

    issue_bonus_reward(
        worker=worker,
        amount=Decimal("100.00"),
        bonus_type="first_order",
        description="Бонус за первый заказ",
    )


def process_high_rating_bonus(worker):
    if worker.rating_avg < Decimal("4.90"):
        return

    exists = BonusReward.objects.filter(
        worker=worker,
        description="Бонус за высокий рейтинг",
    ).exists()

    if exists:
        return

    issue_bonus_reward(
        worker=worker,
        amount=Decimal("500.00"),
        bonus_type="rating",
        description="Бонус за высокий рейтинг",
    )


def process_daily_orders_bonus(worker):
    if worker.orders_count < 10:
        return

    exists = BonusReward.objects.filter(
        worker=worker,
        description="Бонус за 10 заказов",
    ).exists()

    if exists:
        return

    issue_bonus_reward(
        worker=worker,
        amount=Decimal("300.00"),
        bonus_type="orders",
        description="Бонус за 10 заказов",
    )