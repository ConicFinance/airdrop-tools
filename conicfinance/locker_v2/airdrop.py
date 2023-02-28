import datetime as dt
import gzip
import json
from collections import defaultdict
from decimal import Decimal
from os import path
from typing import Dict
import math


DATA_PATH = path.join(path.dirname(__file__), "../../data")

CNC_LOCK_EVENTS = path.join(DATA_PATH, "cnc-locker-events.jsonl.gz")
CNC_LOCK_EVENT_TIMES = path.join(DATA_PATH, "cnc-locker-event-times.json")
LOCKED_CRV = path.join(DATA_PATH, "airdrop-boost-vecrv-balances.json.gz")


MULTIPLIER = 10**18

# 100 CNC locked for 4 months cutoff
CNC_CUTOFF = 86400 * 120 * 100 * MULTIPLIER
CRV_CUTOFF = 100 * MULTIPLIER

LATE_BOOST_TIME = dt.datetime(
    2022, 12, 1, 19, 16, 0, tzinfo=dt.timezone.utc
).timestamp()

LATE_BOOST_MULTIPLIER = 4

MIN_VLCNC_BOOST = Decimal("1")
MAX_VLCNC_BOOST = Decimal("2")

MIN_VCERV_BOOST = Decimal("1.2")
MAX_VECRV_BOOST = Decimal("1.5")

EXCLUDED_ADDRESSES = {
    "0x989AEb4d175e16225E39E87d0D97A3360524AD80",  # CurveVoterProxy
    "0xF147b8125d2ef93FB6965Db97D6746952a133934",  # CurveYCRVVoter
}


def get_total_cnc_locked_per_user():
    with gzip.open(CNC_LOCK_EVENTS) as f:
        events = [json.loads(line) for line in f]
    with open(CNC_LOCK_EVENT_TIMES) as f:
        times = json.load(f)

    total_locked_per_user = {}
    for event in events:
        if event["event"] != "Locked":
            continue

        event_time = times[str(event["blockNumber"])]
        account, amount, unlockTime = event["args"]["account"], event["args"]["amount"], event["args"]["unlockTime"]

        amountTime = amount * (unlockTime - event_time)

        total_locked_per_user.setdefault(account, 0)
        if event_time >= LATE_BOOST_TIME:
            amountTime *= LATE_BOOST_MULTIPLIER
        total_locked_per_user[account] += amountTime

    return total_locked_per_user


def get_total_crv_locked_per_user():
    with gzip.open(LOCKED_CRV) as f:
        return json.load(f)


def flatten(value: Decimal) -> Decimal:
    return value.ln()


def standardize_CRV_boost(value: Decimal, min_value: Decimal, max_value: Decimal) -> Decimal:
    return Decimal(((value - min_value)**Decimal(0.5))/((max_value - min_value)**Decimal(0.5)))

def subtract_min(value:Decimal, min_value:Decimal):
    return Decimal(value - min_value)

def standardize_CNC_boost(value: Decimal, min_result_value: Decimal, max_value: Decimal) -> Decimal:
    return Decimal(((value**(Decimal(0.5))) / (max_value **(Decimal(0.5)))) + min_result_value)

def compute_CRV_airdrop_boost(
    balances: Dict[str, int], min_boost: Decimal, max_boost: Decimal, cutoff: int
):
    """Compute the airdrop boost for a given set of balances.
    cutoff: minimum amount of tokens required to receive a boost (scaled)
    """
    amount_per_user = {
        k: flatten(Decimal(v) / MULTIPLIER) for k, v in balances.items() if v >= cutoff
    }

    min_amount = min(amount_per_user.values())
    max_amount = max(amount_per_user.values())
    standardized_amounts = {
        k: standardize_CRV_boost(v, min_amount, max_amount) for k, v in amount_per_user.items()
    }

    return defaultdict(
        lambda: 1,
        {
            k: min_boost + v * (max_boost - min_boost)
            for k, v in standardized_amounts.items()
        },
    )

def compute_CNC_airdrop_boost(
    balances: Dict[str, int], cutoff: int
):
    """Compute the airdrop boost for a given set of balances.
    cutoff: minimum amount of tokens required to receive a boost (scaled)
    """
    amount_per_user = {
        k: flatten(Decimal(v) / MULTIPLIER) for k, v in balances.items() if v >= cutoff
    }

    min_amount = min(amount_per_user.values())
    min_subbed_amounts = {
        k: subtract_min(v, min_amount) for k, v in amount_per_user.items()
    }
    max_amount = max(min_subbed_amounts.values())
    standardized_amounts = {
        k: standardize_CNC_boost(v, MIN_VLCNC_BOOST, max_amount) for k, v in min_subbed_amounts.items()
    }

    return defaultdict(
        lambda: 1,
        {
            k: v 
            for k, v in standardized_amounts.items()
        },
    )


def compute_vlcnc_airdrop_boost():
    balances = get_total_cnc_locked_per_user()
    return compute_CNC_airdrop_boost(balances, CNC_CUTOFF)


def compute_vecrv_airdrop():
    balances = {
        account: int(item["balance"])
        for item in get_total_crv_locked_per_user()
        if (account := item["address"]) not in EXCLUDED_ADDRESSES
    }
    return compute_CRV_airdrop_boost(balances, MIN_VCERV_BOOST, MAX_VECRV_BOOST, CRV_CUTOFF)


def compute_airdrop():
    vlcnc_boost = compute_vlcnc_airdrop_boost()
    vecrv_boost = compute_vecrv_airdrop()

    return [
        {
            "address": k,
            "value": int(vlcnc_boost[k] * vecrv_boost[k] * MULTIPLIER),
            "vlcnc_boost": float(vlcnc_boost[k]),
            "vecrv_boost": float(vecrv_boost[k]),
        }
        for k in vlcnc_boost.keys() | vecrv_boost.keys()
    ]
