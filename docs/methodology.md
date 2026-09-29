# Methodology

This repository is a public-safe demonstration of explainable fraud-risk analytics. It does not reproduce any bank, exchange, or employer's internal fraud rules, thresholds, features, customer data, or models.

## Signals

| Rule | Illustrative trigger | Weight |
|---|---|---:|
| `HIGH_AMOUNT` | Transaction >= KRW 2,000,000 | 25 |
| `AMOUNT_SPIKE` | Large deviation from customer median | 30 |
| `NEW_COUNTRY` | Country outside observed baseline | 30 |
| `NEW_DEVICE` | Device outside observed baseline | 20 |
| `HIGH_RISK_MERCHANT` | Illustrative high-risk MCC set | 35 |
| `VELOCITY_SPIKE` | 5+ transactions in 10 minutes | 40 |
| `RAPID_CASHOUT_PATTERN` | Card activity followed quickly by large ATM/transfer outflow | 30 |

Scores are additive and capped at 100.

## Why rules instead of a black-box model?

For a control-oriented portfolio project, explainability is useful: reviewers can see exactly why an alert fired, which assumptions matter, and how thresholds could be governed.

## Synthetic evaluation

The generator injects labeled scenarios. Precision/recall produced by the pipeline measure behavior only against those injected labels and are not real-world performance claims.

## Production extensions

A production implementation would normally add:
- customer segmentation and peer groups
- account tenure and KYC context
- merchant/device reputation
- graph features
- model calibration
- case-management feedback loops
- threshold governance
- drift monitoring
- fairness and explainability controls
