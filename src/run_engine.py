from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from .risk_engine import add_risk_scores, alerts_only
    from .rules import RULE_WEIGHTS, apply_rules
except ImportError:
    from risk_engine import add_risk_scores, alerts_only
    from rules import RULE_WEIGHTS, apply_rules


def evaluate_synthetic(df: pd.DataFrame, threshold: int) -> dict:
    truth = df["is_injected_fraud"].astype(int) == 1
    pred = df["risk_score"] >= threshold

    tp = int((truth & pred).sum())
    fp = int((~truth & pred).sum())
    fn = int((truth & ~pred).sum())
    tn = int((~truth & ~pred).sum())

    return {
        "note": "Evaluation uses injected synthetic labels only; it is not a real-world fraud accuracy claim.",
        "true_positive_transactions": tp,
        "false_positive_transactions": fp,
        "false_negative_transactions": fn,
        "true_negative_transactions": tn,
        "precision": round(tp / (tp + fp), 4) if (tp + fp) else 0.0,
        "recall": round(tp / (tp + fn), 4) if (tp + fn) else 0.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sample_transactions.csv")
    parser.add_argument("--output", default="output/sample_alerts.csv")
    parser.add_argument("--summary", default="output/summary.json")
    parser.add_argument("--minimum-score", type=int, default=30)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    ruled = apply_rules(df)
    scored = add_risk_scores(ruled)
    alerts = alerts_only(scored, args.minimum_score)

    out = alerts.copy()
    out["rules"] = out["rules"].apply(lambda x: "|".join(x))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)

    summary = {
        "transactions_analyzed": int(len(scored)),
        "alerts_generated": int(len(alerts)),
        "alert_rate": round(len(alerts) / len(scored), 4) if len(scored) else 0.0,
        "rule_weights": RULE_WEIGHTS,
        "synthetic_evaluation": evaluate_synthetic(scored, args.minimum_score),
    }
    Path(args.summary).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
