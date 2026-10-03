"""
upay AI Shield - Automated Dataset Validation Script
Validates data integrity, schema consistency, missing values, duplicates,
referential integrity, numeric ranges, and class distributions.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np

# Ensure UTF-8 stdout if possible
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DataValidator")


def validate_datasets(
    tx_path: str = "data/raw/upay_ai_shield_20000_transactions.csv",
    cust_path: str = "data/raw/upay_ai_shield_5000_customers.csv",
    pred_path: str = "data/raw/upay_ai_shield_20000_risk_predictions.csv"
) -> dict:
    # Resolve fallbacks
    for path_var, name in [(tx_path, "upay_ai_shield_20000_transactions.csv"),
                          (cust_path, "upay_ai_shield_5000_customers.csv"),
                          (pred_path, "upay_ai_shield_20000_risk_predictions.csv")]:
        if not os.path.exists(path_var) and os.path.exists(name):
            if path_var == tx_path: tx_path = name
            elif path_var == cust_path: cust_path = name
            elif path_var == pred_path: pred_path = name

    print("\n" + "=" * 70)
    print("UPAY AI SHIELD -- AUTOMATED DATASET INTEGRITY & VALIDATION AUDIT")
    print("=" * 70)

    report = {"status": "PASSED", "checks": {}, "errors": [], "warnings": []}

    # 1. Load Data
    print("\n[1/7] Loading Datasets...")
    try:
        df_tx = pd.read_csv(tx_path)
        df_cust = pd.read_csv(cust_path)
        df_pred = pd.read_csv(pred_path)
        print(f"  [OK] Transactions: {df_tx.shape[0]:,} rows x {df_tx.shape[1]} columns")
        print(f"  [OK] Customers:    {df_cust.shape[0]:,} rows x {df_cust.shape[1]} columns")
        print(f"  [OK] Predictions:  {df_pred.shape[0]:,} rows x {df_pred.shape[1]} columns")
        report["checks"]["dataset_shapes"] = {
            "transactions": df_tx.shape,
            "customers": df_cust.shape,
            "predictions": df_pred.shape
        }
    except Exception as e:
        report["status"] = "FAILED"
        report["errors"].append(f"Failed to load CSVs: {e}")
        print(f"  [ERROR] {e}")
        return report

    # 2. Missing Value Check
    print("\n[2/7] Checking for Missing / Null Values...")
    tx_nulls = df_tx.isnull().sum()
    total_nulls = int(tx_nulls.sum())
    if total_nulls == 0:
        print("  [OK] Zero missing values detected across all transaction columns.")
    else:
        print(f"  [WARN] {total_nulls} missing values found.")
        report["warnings"].append(f"{total_nulls} nulls in transactions")
    report["checks"]["total_missing_values"] = total_nulls

    # 3. Duplicate IDs Check
    print("\n[3/7] Checking for Duplicate Identifiers...")
    tx_dupes = int(df_tx.duplicated(subset=["transaction_id"]).sum())
    cust_dupes = int(df_cust.duplicated(subset=["customer_id"]).sum())
    print(f"  [OK] Duplicate Transaction IDs: {tx_dupes}")
    print(f"  [OK] Duplicate Customer IDs:    {cust_dupes}")
    if tx_dupes > 0 or cust_dupes > 0:
        report["errors"].append(f"Duplicate IDs found: tx={tx_dupes}, cust={cust_dupes}")
        report["status"] = "FAILED"
    report["checks"]["duplicates"] = {"transactions": tx_dupes, "customers": cust_dupes}

    # 4. Referential Integrity (Transactions -> Customers)
    print("\n[4/7] Checking Referential Integrity...")
    tx_customers = set(df_tx["customer_id"].dropna().unique())
    known_customers = set(df_cust["customer_id"].dropna().unique())
    orphaned_customers = tx_customers - known_customers
    if len(orphaned_customers) == 0:
        print(f"  [OK] All {len(tx_customers):,} transaction customer IDs exist in customers master table.")
    else:
        print(f"  [WARN] {len(orphaned_customers)} customer IDs in transactions not in customer registry.")
        report["warnings"].append(f"{len(orphaned_customers)} orphaned customer IDs")
    report["checks"]["orphaned_customers_count"] = len(orphaned_customers)

    # 5. Numeric Boundary & Domain Range Validation
    print("\n[5/7] Checking Value Boundaries & Ranges...")
    range_checks = {
        "amount": (df_tx["amount"] >= 0).all(),
        "hour": (df_tx["hour"].between(0, 23)).all(),
        "day_of_week": (df_tx["day_of_week"].between(0, 6)).all(),
        "is_new_receiver": (df_tx["is_new_receiver"].isin([0, 1])).all(),
        "is_new_device": (df_tx["is_new_device"].isin([0, 1])).all(),
        "location_changed": (df_tx["location_changed"].isin([0, 1])).all(),
        "transactions_last_1h": (df_tx["transactions_last_1h"] >= 0).all(),
        "transactions_last_24h": (df_tx["transactions_last_24h"] >= 0).all(),
        "failed_attempts": (df_tx["failed_attempts"] >= 0).all(),
        "account_age_days": (df_tx["account_age_days"] >= 0).all(),
        "amount_deviation": (df_tx["amount_deviation"] >= 0).all()
    }
    all_ranges_valid = True
    for feat, valid in range_checks.items():
        if valid:
            print(f"  [OK] {feat:<28} range valid [min={df_tx[feat].min():.2f}, max={df_tx[feat].max():.2f}]")
        else:
            print(f"  [ERROR] {feat:<28} OUT OF RANGE!")
            all_ranges_valid = False
            report["errors"].append(f"Feature {feat} contains out-of-range values.")
    report["checks"]["range_validation"] = "PASSED" if all_ranges_valid else "FAILED"

    # 6. Target Distribution & Label Analysis
    print("\n[6/7] Validating Target Class & Risk Labels...")
    target_counts = df_tx["is_fraud"].value_counts().to_dict()
    target_pct = df_tx["is_fraud"].value_counts(normalize=True).to_dict()
    print(f"  [OK] Synthetic Target 'is_fraud':")
    print(f"      - Legitimate (0): {target_counts.get(0, 0):,} ({target_pct.get(0, 0):.2%})")
    print(f"      - Synthetic Flag (1): {target_counts.get(1, 0):,} ({target_pct.get(1, 0):.2%})")
    
    risk_levels = df_tx["risk_level"].value_counts().to_dict()
    print(f"  [OK] Risk Levels: {risk_levels}")
    report["checks"]["target_distribution"] = {
        "synthetic_label": "is_fraud",
        "counts": {str(k): int(v) for k, v in target_counts.items()},
        "percentages": {str(k): round(float(v) * 100, 2) for k, v in target_pct.items()}
    }

    # 7. Summary
    print("\n[7/7] Dataset Audit Complete!")
    if report["status"] == "PASSED" and not report["errors"]:
        print("\n[SUCCESS] RESULT: DATASET INTEGRITY VERIFIED. 100% READY FOR ML & PRODUCTION PIPELINE.\n")
    else:
        print("\n[FAILED] RESULT: VALIDATION ISSUES DETECTED.\n")

    return report


if __name__ == "__main__":
    report = validate_datasets()
