from __future__ import annotations

import pandas as pd


RULE_WEIGHTS = {
    "HIGH_AMOUNT": 25,
    "AMOUNT_SPIKE": 30,
    "NEW_COUNTRY": 30,
    "NEW_DEVICE": 20,
    "HIGH_RISK_MERCHANT": 35,
    "VELOCITY_SPIKE": 40,
    "RAPID_CASHOUT_PATTERN": 30,
}

HIGH_AMOUNT_THRESHOLD = 2_000_000
VELOCITY_WINDOW_MINUTES = 10
VELOCITY_COUNT_THRESHOLD = 5
HIGH_RISK_MCC = {"4829", "6011", "7995"}


def build_customer_baselines(df: pd.DataFrame) -> dict[str, dict]:
    work = df.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"])

    clean = work[work["is_injected_fraud"].astype(int) == 0]
    baselines = {}

    for customer_id, group in clean.groupby("customer_id"):
        median_amount = float(group["amount"].median()) if len(group) else 0.0
        countries = set(group["country"].dropna().astype(str))
        devices = set(group["device_id"].dropna().astype(str))

        baselines[customer_id] = {
            "median_amount": median_amount,
            "countries": countries,
            "devices": devices,
        }

    return baselines


def detect_event_rules(
    df: pd.DataFrame, baselines: dict[str, dict]
) -> pd.DataFrame:
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"])
    rule_lists: list[list[str]] = []

    for row in out.itertuples(index=False):
        rules = []
        baseline = baselines.get(row.customer_id, {})
        median_amount = float(baseline.get("median_amount") or 0.0)

        if float(row.amount) >= HIGH_AMOUNT_THRESHOLD:
            rules.append("HIGH_AMOUNT")

        if median_amount > 0 and float(row.amount) >= max(500_000, median_amount * 6):
            rules.append("AMOUNT_SPIKE")

        known_countries = baseline.get("countries") or set()
        if known_countries and str(row.country) not in known_countries:
            rules.append("NEW_COUNTRY")

        known_devices = baseline.get("devices") or set()
        if known_devices and str(row.device_id) not in known_devices:
            rules.append("NEW_DEVICE")

        if str(row.merchant_category_code) in HIGH_RISK_MCC:
            rules.append("HIGH_RISK_MERCHANT")

        rule_lists.append(rules)

    out["rules"] = rule_lists
    return out


def mark_velocity_spikes(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values(["customer_id", "timestamp"]).reset_index(drop=True)
    out["timestamp"] = pd.to_datetime(out["timestamp"])
    flag = pd.Series(False, index=out.index)
    window = pd.Timedelta(minutes=VELOCITY_WINDOW_MINUTES)

    for _, indexes in out.groupby("customer_id").groups.items():
        indexes = list(indexes)
        left = 0

        for right in range(len(indexes)):
            right_idx = indexes[right]
            right_ts = out.at[right_idx, "timestamp"]

            while left <= right:
                left_idx = indexes[left]
                if right_ts - out.at[left_idx, "timestamp"] <= window:
                    break
                left += 1

            window_indexes = indexes[left : right + 1]
            if len(window_indexes) >= VELOCITY_COUNT_THRESHOLD:
                flag.loc[window_indexes] = True

    for idx in out.index[flag]:
        rules = list(out.at[idx, "rules"])
        if "VELOCITY_SPIKE" not in rules:
            rules.append("VELOCITY_SPIKE")
        out.at[idx, "rules"] = rules

    return out


def mark_rapid_cashout(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values(["customer_id", "timestamp"]).reset_index(drop=True)
    out["timestamp"] = pd.to_datetime(out["timestamp"])

    for _, group in out.groupby("customer_id"):
        indexes = list(group.index)
        for i, idx in enumerate(indexes):
            if out.at[idx, "channel"] != "card":
                continue

            start_ts = out.at[idx, "timestamp"]
            amount = float(out.at[idx, "amount"])

            for next_idx in indexes[i + 1 :]:
                delta = out.at[next_idx, "timestamp"] - start_ts
                if delta > pd.Timedelta(minutes=30):
                    break

                if (
                    out.at[next_idx, "channel"] in {"atm", "transfer"}
                    and float(out.at[next_idx, "amount"]) >= amount * 0.7
                ):
                    for target_idx in (idx, next_idx):
                        rules = list(out.at[target_idx, "rules"])
                        if "RAPID_CASHOUT_PATTERN" not in rules:
                            rules.append("RAPID_CASHOUT_PATTERN")
                        out.at[target_idx, "rules"] = rules
                    break

    return out


def apply_rules(df: pd.DataFrame) -> pd.DataFrame:
    baselines = build_customer_baselines(df)
    out = detect_event_rules(df, baselines)
    out = mark_velocity_spikes(out)
    out = mark_rapid_cashout(out)
    return out
