import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

results = []


def check(label, ok, detail="", level="FAIL"):
    status = "PASS" if ok else level
    results.append(status)
    print(f"  {status:<6}{label}" + (f" ({detail})" if detail else ""))


def main():
    raw_hrrp = pd.read_csv(RAW_DIR / "hrrp_fy2026.csv", dtype=str)
    raw_hosp = pd.read_csv(RAW_DIR / "hospital_general_info.csv", dtype=str)
    hrrp = pd.read_parquet(PROCESSED_DIR / "hrrp.parquet")
    hosp = pd.read_parquet(PROCESSED_DIR / "hospitals.parquet")

    print("Row counts")
    check("hrrp: raw = processed", len(raw_hrrp) == len(hrrp), f"{len(raw_hrrp):,} vs {len(hrrp):,}")
    check("hospitals: raw = processed", len(raw_hosp) == len(hosp), f"{len(raw_hosp):,} vs {len(hosp):,}")
    raw_suppressed = raw_hrrp["Number of Readmissions"].eq("Too Few to Report").sum()
    suppressed = hrrp["is_suppressed"]
    check("is_suppressed = raw 'Too Few to Report'", suppressed.sum() == raw_suppressed, f"{raw_suppressed:,}")
    counted = hrrp["Number of Readmissions"].notna()
    unreported = ~hrrp["is_reported"]
    buckets = counted.astype(int) + suppressed.astype(int) + unreported.astype(int)
    check("each row is counted, suppressed, or unreported", buckets.eq(1).all(),
          f"{counted.sum():,} + {suppressed.sum():,} + {unreported.sum():,}")

    print("Nulls and keys")
    check("no null Facility IDs", hrrp["Facility ID"].notna().all() and hosp["Facility ID"].notna().all())
    check("hrrp: one row per facility + measure", not hrrp.duplicated(["Facility ID", "Measure Name"]).any())
    check("hospitals: one row per facility", hosp["Facility ID"].is_unique)
    rates = ["Predicted Readmission Rate", "Expected Readmission Rate"]
    check("reported rows have both rates", hrrp.loc[hrrp["is_reported"], rates].notna().all(axis=None))
    missing = ~hrrp["Facility ID"].isin(hosp["Facility ID"])
    check("hrrp facilities exist in hospitals file", not missing.any(),
          f"{hrrp.loc[missing, 'Facility ID'].nunique()} facilities, {missing.sum()} rows", level="WARN")

    print("Ranges")
    err = hrrp["Excess Readmission Ratio"].dropna()
    check("excess readmission ratio > 0", err.gt(0).all(), f"{err.min():.2f} to {err.max():.2f}")
    for col in rates:
        vals = hrrp[col].dropna()
        check(f"{col.lower()} within 0-100", vals.between(0, 100).all(), f"{vals.min():.1f} to {vals.max():.1f}")
    check("discharges >= 0", hrrp["Number of Discharges"].dropna().ge(0).all())
    check("readmissions <= discharges", not (hrrp["Number of Readmissions"] > hrrp["Number of Discharges"]).any())
    windows = hrrp[["Start Date", "End Date"]].drop_duplicates()
    check("single reporting window", len(windows) == 1 and (windows["Start Date"] < windows["End Date"]).all(),
          f"{hrrp['Start Date'].min():%Y-%m-%d} to {hrrp['End Date'].max():%Y-%m-%d}")

    fails = results.count("FAIL")
    print(f"\nPASS {results.count('PASS')} | FAIL {fails} | WARN {results.count('WARN')}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
