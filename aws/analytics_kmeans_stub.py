#!/usr/bin/env python3
import argparse, io, os, sys, math
from collections import Counter

import boto3
import pandas as pd
import numpy as np

# ---------- utils ----------
def s3_read_csv(s3, bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    return pd.read_csv(io.BytesIO(obj["Body"].read()))

def year_to_age(y, ref_year=2025):
    try:
        y = int(y)
        if y <= 0 or y > ref_year: return np.nan
        age = ref_year - y
        # sane range
        if age < 0 or age > 120: return np.nan
        return age
    except Exception:
        return np.nan

def gender_to_num(g):
    g = str(g or "").upper().strip()
    return {"M":0, "F":1, "O":2, "UNK":3}.get(g, 3)

def zscore(df, cols):
    df = df.copy()
    for c in cols:
        mu = df[c].mean()
        sd = df[c].std(ddof=0)
        df[c] = 0.0 if (sd == 0 or np.isnan(sd)) else (df[c] - mu) / sd
    return df

def kmeans_numpy(X, k, iters=100, seed=42):
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    # choose distinct initial centers
    idx = rng.choice(n, size=k, replace=False)
    centers = X[idx].copy()
    assign = np.zeros(n, dtype=int)

    for _ in range(iters):
        # assign
        dists = np.linalg.norm(X[:, None, :] - centers[None, :, :], axis=2)  # (n, k)
        new_assign = dists.argmin(axis=1)
        if np.array_equal(new_assign, assign):
            break
        assign = new_assign
        # update
        for j in range(k):
            pts = X[assign == j]
            if len(pts) > 0:
                centers[j] = pts.mean(axis=0)
            else:
                # re-seed empty cluster
                centers[j] = X[rng.integers(0, n)]
    return assign

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", required=True)
    ap.add_argument("--k", type=int, default=3)
    args = ap.parse_args()

    s3 = boto3.client("s3")

    # Read curated inputs produced by the pipeline
    person = s3_read_csv(s3, args.bucket, "curated/person/person.csv")
    cond   = s3_read_csv(s3, args.bucket, "curated/condition_occurrence/condition_occurrence.csv")
    obs    = s3_read_csv(s3, args.bucket, "curated/observation/observation.csv")

    # Basic derived features
    # person: person_id, year_of_birth, gender_concept_code -> age, gender_num
    dfp = person.copy()
    ycol = "year_of_birth" if "year_of_birth" in dfp.columns else "birth_datetime"
    dfp["age"] = dfp[ycol].map(year_to_age)
    dfp["gender_num"] = dfp["gender_concept_code"].map(gender_to_num)

    # observation counts per person
    ob = obs.groupby("person_id", as_index=False).size().rename(columns={"size":"obs_count"})
    # distinct condition codes per person
    co = cond.groupby("person_id", as_index=False)["condition_concept_code"].nunique().rename(
        columns={"condition_concept_code":"cond_nunique"}
    )

    # merge
    feat = dfp[["person_id","age","gender_num"]].merge(ob, on="person_id", how="left").merge(co, on="person_id", how="left")
    # fill missing counts with 0, age with median
    feat["obs_count"] = feat["obs_count"].fillna(0).astype(float)
    feat["cond_nunique"] = feat["cond_nunique"].fillna(0).astype(float)
    if feat["age"].isna().all():
        # if all ages missing, set to 0 so we can still cluster on other dims
        feat["age"] = 0.0
    else:
        feat["age"] = feat["age"].fillna(feat["age"].median())

    # drop rows that are totally empty after fill (extremely unlikely)
    feat = feat.dropna(subset=["age","gender_num","obs_count","cond_nunique"])

    # If too few rows, print diagnostics and exit gracefully
    n = len(feat)
    if n < 3:
        print("Not enough rows for meaningful clustering. Diagnostics:")
        print(feat.head(10).to_string(index=False))
        # still write minimal outputs so the pipeline doesn’t break
        out = feat[["person_id"]].copy()
        out["cluster"] = 0
        _write_outputs(out, args.bucket)
        return

    # scale numeric columns
    cols = ["age","gender_num","obs_count","cond_nunique"]
    feat_scaled = zscore(feat, cols)

    X = feat_scaled[cols].to_numpy(dtype=float)
    k = min(max(1, args.k), n)  # ensure 1 <= k <= n
    assign = kmeans_numpy(X, k=k, iters=100, seed=42)

    out = feat[["person_id"]].copy()
    out["cluster"] = assign

    _write_outputs(out, args.bucket)

def _write_outputs(assign_df, bucket):
    # S3 CSV
    csv_bytes = assign_df.to_csv(index=False).encode("utf-8")
    boto3.client("s3").put_object(
        Bucket=bucket,
        Key="analytics/kmeans/assignments.csv",
        Body=csv_bytes,
        ContentType="text/csv",
        ServerSideEncryption="AES256"
    )
    print(f"Wrote s3://{bucket}/analytics/kmeans/assignments.csv")

    # Local copy for quick inspection
    os.makedirs("reports", exist_ok=True)
    assign_df.to_csv("reports/cluster_assignments.csv", index=False)
    print("Wrote reports/cluster_assignments.csv\n")
    # Show sizes
    sizes = assign_df["cluster"].value_counts().sort_index()
    print("Cluster sizes:")
    print(sizes.rename_axis("cluster").reset_index(name="n").to_string(index=False))

if __name__ == "__main__":
    main()
