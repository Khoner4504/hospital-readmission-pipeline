from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

SUPPRESSED = "Too Few to Report"


def clean_hrrp(path=RAW_DIR / "hrrp_fy2026.csv"):
    # Rule 1: keep leading zeros (010001). pandas reads the file's "N/A" as null.
    df = pd.read_csv(path, dtype={"Facility ID": str})

    # Rule 2: flag suppressed counts, then null them so the column can be numeric
    df["is_suppressed"] = df["Number of Readmissions"].eq(SUPPRESSED)
    df["Number of Readmissions"] = pd.to_numeric(
        df["Number of Readmissions"].mask(df["is_suppressed"])
    ).astype("Int64")

    # Rule 3: keep unreported rows, but flag them. Based on the ratio rather than
    # the footnote, because footnote 29 rows still have results.
    df["is_reported"] = df["Excess Readmission Ratio"].notna()

    # Rule 4
    df["Number of Discharges"] = df["Number of Discharges"].astype("Int64")

    # Rule 5
    for col in ["Start Date", "End Date"]:
        df[col] = pd.to_datetime(df[col], format="%m/%d/%Y")

    return df


def clean_hospitals(path=RAW_DIR / "hospital_general_info.csv"):
    # Rule 1. ZIP Code has the same leading-zero problem (06105 -> 6105).
    return pd.read_csv(path, dtype={"Facility ID": str, "ZIP Code": str})


def main():
    # Rule 6
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in [("hrrp", clean_hrrp()), ("hospitals", clean_hospitals())]:
        out = PROCESSED_DIR / f"{name}.parquet"
        df.to_parquet(out, index=False)
        print(f"wrote {out.relative_to(ROOT)} ({len(df):,} rows)")


if __name__ == "__main__":
    main()
