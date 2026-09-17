import os
from pathlib import Path
import boto3
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BUCKET = os.getenv("S3_BUCKET")
FILES = ["hrrp_fy2026.csv", "hospital_general_info.csv"]

def download_raw(dest_dir=ROOT / "data" / "raw"):
    s3 = boto3.client("s3")
    os.makedirs(dest_dir, exist_ok=True)
    for name in FILES:
        local_path = os.path.join(dest_dir, name)
        s3.download_file(BUCKET, f"raw/{name}", local_path)
        print(f"downloaded {name}")

if __name__ == "__main__":
    download_raw()