import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"
load_dotenv(ROOT / ".env")

CONDITIONS = {
    "AMI": "Heart attack",
    "CABG": "Coronary artery bypass graft surgery",
    "COPD": "Chronic obstructive pulmonary disease",
    "HF": "Heart failure",
    "HIP-KNEE": "Hip/knee replacement",
    "PN": "Pneumonia",
}


def build_dim_facility(hospitals, hrrp):
    rating = hospitals["Hospital overall rating"]
    dim = pd.DataFrame({
        "facility_id": hospitals["Facility ID"],
        "facility_name": hospitals["Facility Name"],
        "city": hospitals["City/Town"],
        "state": hospitals["State"],
        "zip_code": hospitals["ZIP Code"],
        "county": hospitals["County/Parish"],
        "hospital_type": hospitals["Hospital Type"],
        "hospital_ownership": hospitals["Hospital Ownership"],
        "emergency_services": hospitals["Emergency Services"].eq("Yes"),
        "overall_rating": pd.to_numeric(rating.mask(rating.eq("Not Available"))).astype("Int64"),
        "record_source": "hospital_info",
    })

    # Facilities missing from the hospital file keep their readmission rows
    # through a fallback dim row built from the HRRP file's name and state.
    missing = hrrp[~hrrp["Facility ID"].isin(dim["facility_id"])].drop_duplicates("Facility ID")
    fallback = pd.DataFrame({
        "facility_id": missing["Facility ID"],
        "facility_name": missing["Facility Name"],
        "state": missing["State"],
        "record_source": "hrrp_fallback",
    })
    return pd.concat([dim, fallback], ignore_index=True)


def build_dim_measure(hrrp):
    ids = pd.Series(sorted(hrrp["Measure Name"].unique()))
    codes = ids.str.removeprefix("READM-30-").str.removesuffix("-HRRP")
    unknown = set(codes) - set(CONDITIONS)
    if unknown:
        raise ValueError(f"no condition name for measure codes: {unknown}")
    return pd.DataFrame({"measure_id": ids, "measure_code": codes, "condition_name": codes.map(CONDITIONS)})


def build_fact(hrrp):
    return pd.DataFrame({
        "facility_id": hrrp["Facility ID"],
        "measure_id": hrrp["Measure Name"],
        "start_date": hrrp["Start Date"].dt.date,
        "end_date": hrrp["End Date"].dt.date,
        "number_of_discharges": hrrp["Number of Discharges"],
        "number_of_readmissions": hrrp["Number of Readmissions"],
        "excess_readmission_ratio": hrrp["Excess Readmission Ratio"],
        "predicted_readmission_rate": hrrp["Predicted Readmission Rate"],
        "expected_readmission_rate": hrrp["Expected Readmission Rate"],
        "footnote": hrrp["Footnote"].astype("Int64"),
        "is_suppressed": hrrp["is_suppressed"],
        "is_reported": hrrp["is_reported"],
    })


def main():
    hrrp = pd.read_parquet(PROCESSED_DIR / "hrrp.parquet")
    hospitals = pd.read_parquet(PROCESSED_DIR / "hospitals.parquet")
    tables = {
        "dim_facility": build_dim_facility(hospitals, hrrp),
        "dim_measure": build_dim_measure(hrrp),
        "fact_readmission": build_fact(hrrp),
    }

    # One transaction: if any step fails, the database is left as it was
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.begin() as conn:
        conn.exec_driver_sql((SQL_DIR / "ddl" / "01_tables.sql").read_text())
        for name, df in tables.items():
            df.to_sql(name, conn, if_exists="append", index=False, method="multi", chunksize=1000)
            count = conn.execute(text(f"SELECT count(*) FROM {name}")).scalar_one()
            if count != len(df):
                raise RuntimeError(f"{name}: loaded {count:,} rows, expected {len(df):,}")
            print(f"loaded {name} ({count:,} rows)")
        for path in sorted((SQL_DIR / "views").glob("*.sql")):
            conn.exec_driver_sql(path.read_text())
            print(f"created view {path.stem}")


if __name__ == "__main__":
    main()
