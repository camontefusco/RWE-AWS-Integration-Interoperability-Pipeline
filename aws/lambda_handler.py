import json
import os
import io
import hashlib
import logging

import boto3
import pandas as pd

from pipeline.transform import transform_df  # existing mapping logic

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")

# ---------------------- De-ID helpers ---------------------------------------
def _salt() -> str:
    # configurable via env; demo default
    return os.getenv("PSEUD_ID_SALT", "demo-salt")

def pseudonymize_value(value: str) -> str:
    """Return a reproducible salted hash for an identifier-like value."""
    h = hashlib.sha256()
    h.update(_salt().encode("utf-8"))
    h.update(str(value).encode("utf-8"))
    return h.hexdigest()  # 64 hex chars

PHI_COLS = {"name", "address", "email", "phone", "ssn"}

def deidentify(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Drop obvious PHI columns if present
    for c in list(df.columns):
        if c.lower() in PHI_COLS:
            df.drop(columns=[c], inplace=True, errors="ignore")

    # Pseudonymize person_id if present
    if "person_id" in df.columns:
        df["person_id"] = df["person_id"].astype(str).map(pseudonymize_value)

    # Example: if you had full DOB, truncate to year:
    # if "date_of_birth" in df.columns:
    #     df["year_of_birth"] = pd.to_datetime(df["date_of_birth"], errors="coerce").dt.year
    #     df.drop(columns=["date_of_birth"], inplace=True)

    return df
# ---------------------------------------------------------------------------

def _read_csv_from_s3(bucket: str, key: str) -> pd.DataFrame:
    logger.info("Reading raw object s3://%s/%s", bucket, key)
    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read()
    return pd.read_csv(io.BytesIO(body))

def _write_bytes(bucket: str, key: str, data: bytes, content_type="text/plain"):
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
        ServerSideEncryption="AES256",  # SSE-S3
    )
    logger.info("Wrote s3://%s/%s", bucket, key)

def handler(event, context):
    """
    Handles S3 PUT triggers or manual invoke payload:
      {"bucket":"my-bucket","keys":["raw/sample_rwd.csv"]}
    """
    logger.info("Event: %s", json.dumps(event))

    bucket = os.environ["BUCKET"]
    curated_prefix = os.environ.get("CURATED_PREFIX", "curated/")
    fhir_prefix = os.environ.get("FHIR_PREFIX", "fhir/")

    # Collect keys to process
    keys = []

    # S3 trigger path
    if "Records" in event:
        for rec in event["Records"]:
            if rec.get("eventSource") == "aws:s3":
                b = rec["s3"]["bucket"]["name"]
                k = rec["s3"]["object"]["key"]
                if b == bucket and k.startswith("raw/"):
                    keys.append(k)

    # Manual invoke path
    if "keys" in event:
        keys.extend(event["keys"])

    if not keys:
        logger.warning("No keys to process; exiting.")
        return {"processed": 0}

    processed = 0
    for key in keys:
        try:
            df_raw = _read_csv_from_s3(bucket, key)
            df_clean = deidentify(df_raw)    # << De-ID here
            outputs = transform_df(df_clean) # returns {'curated':{...}, 'fhir':{...}} of bytes

            # Write curated CSVs
            for rel_key, content in outputs["curated"].items():
                _write_bytes(bucket, f"{curated_prefix}{rel_key}", content, "text/csv")

            # Write FHIR NDJSON
            for rel_key, content in outputs["fhir"].items():
                _write_bytes(bucket, f"{fhir_prefix}{rel_key}", content, "application/x-ndjson")

            processed += 1
        except Exception as e:
            logger.exception("Failed processing %s: %s", key, e)

    return {"processed": processed}
