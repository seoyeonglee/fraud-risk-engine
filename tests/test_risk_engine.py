import pandas as pd

from src.risk_engine import add_risk_scores, severity_for


def test_score_caps_at_100():
    df = pd.DataFrame([{
        "rules": [
            "HIGH_AMOUNT",
            "AMOUNT_SPIKE",
            "NEW_COUNTRY",
            "NEW_DEVICE",
            "HIGH_RISK_MERCHANT",
            "VELOCITY_SPIKE",
        ]
    }])
    out = add_risk_scores(df)
    assert out.loc[0, "risk_score"] == 100
    assert out.loc[0, "severity"] == "critical"


def test_severity_bands():
    assert severity_for(0) == "none"
    assert severity_for(20) == "low"
    assert severity_for(30) == "medium"
    assert severity_for(60) == "high"
    assert severity_for(80) == "critical"
