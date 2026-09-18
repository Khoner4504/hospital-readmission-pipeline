import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "dashboard" / "data"
load_dotenv(ROOT / ".env")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        views = conn.execute(text(
            "SELECT table_name FROM information_schema.views WHERE table_schema = 'public' ORDER BY 1"
        )).scalars().all()
        for view in views:
            # numpy_nullable keeps count columns with blanks as integers (137, not 137.0)
            df = pd.read_sql(text(f'SELECT * FROM "{view}"'), conn, dtype_backend="numpy_nullable")
            # Sort so re-exports only change when the data does
            df = df.sort_values(list(df.columns), ignore_index=True)
            out = OUT_DIR / f"{view}.csv"
            df.to_csv(out, index=False)
            print(f"wrote {out.relative_to(ROOT)} ({len(df):,} rows)")


if __name__ == "__main__":
    main()
