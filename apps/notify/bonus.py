from .services import PushService


def mission_completed(progress):
    return PushService.send(
        user=progress.worker,
        event_type="mission_completed",
        event_key=f"mission_completed_{progress.id}",
        title="Миссия выполнена 🎉",
        message=f"Вы получили бонус {progress.mission.reward_amount} сом",
        payload={
            "type": "navigate",
            "screen": "Wallet",
            "mission_id": progress.mission_id,
        }
    )


def bonus_reward_created(reward):
    return PushService.send(
        user=reward.worker,
        event_type="bonus_reward",
        event_key=f"bonus_reward_{reward.id}",
        title="Начислен бонус 💰",
        message=f"{reward.amount} сом зачислено на ваш баланс",
        payload={
            "type": "navigate",
            "screen": "Wallet",
            "bonus_reward_id": reward.id,
        }
    )


def bonus_rule_completed(worker, rule, amount):
    return PushService.send(
        user=worker,
        event_type="bonus_rule_completed",
        event_key=f"bonus_rule_completed_{worker.id}_{rule.id}",
        title="Бонус получен 🎁",
        message=f"Вы выполнили условие «{rule.title}» и получили {amount} сом",
        payload={
            "type": "navigate",
            "screen": "Wallet",
            "rule_id": rule.id,
        }
    )


from apps.users.models import User

def deposit_success(user, amount):
    return PushService.send(
        user=user,
        event_type="wallet_deposit",
        event_key=f"wallet_deposit_{user.id}",
        title="Пополнение баланса 💰",
        message=f"На ваш баланс зачислено {amount} сом",
        payload={
            "type": "navigate",
            "screen": "Wallet",
        }
    )