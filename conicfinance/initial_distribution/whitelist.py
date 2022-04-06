from decimal import Decimal
import gzip
import json
from os import path

DATA_PATH = path.join(path.dirname(__file__), "../../data")

VECRV_HOLDERS = path.join(DATA_PATH, "vecrv-holder-balances.json.gz")
CUT_OFF_CRV = Decimal(100) * 10**18

CUT_OFF_CVX = Decimal(3) * 10**18
VLCVX_HOLDERS = path.join(DATA_PATH, "vlcvx-snapshot-balances.json.gz")

OG_WHITELIST = path.join(DATA_PATH, "og_whitelist.txt")


def generate(output_file: str):
    users = set()
    for cutoff, filename in zip(
        [CUT_OFF_CRV, CUT_OFF_CVX], [VECRV_HOLDERS, VLCVX_HOLDERS]
    ):
        with gzip.open(filename) as f:
            holders = json.load(f)
        for holder in holders:
            if Decimal(holder["balance"]) >= cutoff:
                users.add(holder["address"])
    with open(OG_WHITELIST) as f:
        for line in f:
            users.add(line.strip())
    with open(output_file, "w") as f:
        json.dump(list(users), f)
