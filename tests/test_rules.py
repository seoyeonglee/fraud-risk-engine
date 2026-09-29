import pandas as pd

from src.rules import apply_rules


def event(**overrides):
    row = {
        "transaction_id": "T1",
        "timestamp": "2026-09-08T10:00:00",
        "customer_id": "C001",
        "amount": 50_000,
        "currency": "KRW",
        "country": "KR",
        "device_id": "D001A",
        "channel": "card",
        "merchant_category_code": "5411",
        "is_injected_fraud": 0,
        "fraud_scenario": "",
    }
    row.update(overrides)
    return row


def baseline_rows():
    return [
        event(
            transaction_id=f"N{i}",
            timestamp=f"2026-09-{(i % 15) + 1:02d}T{9 + (i % 8):02d}:00:00",
            amount=40_000 + i * 500,
        )
        for i in range(20)
    ]


def test_country_device_and_amount_signals():
    rows = baseline_rows()
    rows.append(
        event(
            transaction_id="A1",
            amount=3_000_000,
            country="US",
            device_id="NEW-1",
            merchant_category_code="7995",
            is_injected_fraud=1,
        )
    )
    out = apply_rules(pd.DataFrame(rows))
    rules = out.loc[out["transaction_id"] == "A1", "rules"].iloc[0]

    assert "HIGH_AMOUNT" in rules
    assert "AMOUNT_SPIKE" in rules
    assert "NEW_COUNTRY" in rules
    assert "NEW_DEVICE" in rules
    assert "HIGH_RISK_MERCHANT" in rules


def test_velocity_spike():
    rows = baseline_rows()
    for i in range(5):
        rows.append(
            event(
                transaction_id=f"V{i}",
                timestamp=f"2026-09-20T12:0{i}:00",
                customer_id="C001",
                is_injected_fraud=1,
            )
        )

    out = apply_rules(pd.DataFrame(rows))
    flagged = out[out["transaction_id"].str.startswith("V")]
    assert any("VELOCITY_SPIKE" in rules for rules in flagged["rules"])
