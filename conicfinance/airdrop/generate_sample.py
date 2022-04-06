import random
from decimal import Decimal
from typing import List

from eth_account import Account


def generate_user(amount: int) -> dict:
    address = Account.create().address
    return {"address": address, "value": str(Decimal(amount) * 10**18)}


def generate_users(count: int, total_amount: int) -> List[dict]:
    tiers = [
        (total_amount // 2, count // 10),  # high tier
        (total_amount // 4, count * 4 // 10),  # normal tier
        (total_amount // 4, count * 5 // 10),  # low tier
    ]
    users = []
    for tier_amount, tier_count in tiers:
        user_amount = tier_amount // tier_count
        for _ in range(tier_count):
            users.append(generate_user(user_amount))
    random.shuffle(users)
    return users
