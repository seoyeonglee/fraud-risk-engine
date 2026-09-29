from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


CUSTOMERS = [f"C{i:03d}" for i in range(1, 31)]
COUNTRIES = ["KR", "KR", "KR", "JP", "US"]
MCCS = ["5411", "5812", "5732", "5999", "5311"]


def normal_transaction(rng: random.Random, txn_id: int, base: datetime) -> dict:
    customer_id = rng.choice(CUSTOMERS)
    timestamp = base + timedelta(
        days=rng.randint(0, 20),
        hours=rng.randint(8, 20),
        minutes=rng.randint(0, 59),
    )

    return {
        "transaction_id": f"T{txn_id:05d}",
        "timestamp": timestamp.isoformat(),
        "customer_id": customer_id,
        "amount": rng.randint(10_000, 350_000),
        "currency": "KRW",
        "country": "KR",
        "device_id": f"D{customer_id[1:]}A",
        "channel": rng.choice(["card", "card", "transfer"]),
        "merchant_category_code": rng.choice(MCCS),
        "is_injected_fraud": 0,
        "fraud_scenario": "",
    }


def inject_fraud(rows: list[dict], start_id: int) -> list[dict]:
    fraud = [
        {
            "transaction_id": f"T{start_id:05d}",
            "timestamp": "2026-09-18T02:14:00",
            "customer_id": "C003",
            "amount": 3_500_000,
            "currency": "KRW",
            "country": "US",
            "device_id": "NEW-US-01",
            "channel": "card",
            "merchant_category_code": "7995",
            "is_injected_fraud": 1,
            "fraud_scenario": "high_amount_new_country_device",
        },
        {
            "transaction_id": f"T{start_id+1:05d}",
            "timestamp": "2026-09-18T02:22:00",
            "customer_id": "C003",
            "amount": 3_000_000,
            "currency": "KRW",
            "country": "US",
            "device_id": "NEW-US-01",
            "channel": "transfer",
            "merchant_category_code": "4829",
            "is_injected_fraud": 1,
            "fraud_scenario": "rapid_cashout",
        },
    ]

    next_id = start_id + len(fraud)
    burst_start = datetime.fromisoformat("2026-09-19T12:10:00")

    for i in range(6):
        fraud.append({
            "transaction_id": f"T{next_id+i:05d}",
            "timestamp": (burst_start + timedelta(seconds=i * 50)).isoformat(),
            "customer_id": "C011",
            "amount": 120_000 + i * 10_000,
            "currency": "KRW",
            "country": "KR",
            "device_id": "D011A",
            "channel": "card",
            "merchant_category_code": "5411",
            "is_injected_fraud": 1,
            "fraud_scenario": "velocity_burst",
        })

    fraud.append({
        "transaction_id": f"T{next_id+6:05d}",
        "timestamp": "2026-09-20T15:40:00",
        "customer_id": "C021",
        "amount": 2_800_000,
        "currency": "KRW",
        "country": "JP",
        "device_id": "D021-B",
        "channel": "card",
        "merchant_category_code": "6011",
        "is_injected_fraud": 1,
        "fraud_scenario": "amount_spike_high_risk_merchant",
    })

    return rows + fraud


def generate(seed: int = 42, normal_transactions: int = 500) -> pd.DataFrame:
    rng = random.Random(seed)
    base = datetime(2026, 9, 1)
    rows = [
        normal_transaction(rng, i + 1, base)
        for i in range(normal_transactions)
    ]
    rows = inject_fraud(rows, normal_transactions + 1)
    return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/sample_transactions.csv")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--normal-transactions", type=int, default=500)
    args = parser.parse_args()

    df = generate(args.seed, args.normal_transactions)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"Wrote {len(df)} synthetic transactions to {output}")


if __name__ == "__main__":
    main()
