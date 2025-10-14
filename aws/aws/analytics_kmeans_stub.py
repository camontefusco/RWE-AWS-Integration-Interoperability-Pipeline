#!/usr/bin/env python3
"""
Analytics stub (Stage 4): KMeans-style clustering of curated OMOP-ish person.csv.

- If scikit-learn is available: run real KMeans on [year_of_birth, gender_onehot].
- If not: fall back to simple age-bucket grouping (≤40, 41–60, >60).

Reads:  s3://$BUCKET/curated/person/person.csv
Writes: s3://$BUCKET/analytics/kmeans/assignments.csv
Also writes a local copy to ./reports/cluster_assignments.csv for GitHub.
"""
import argparse, os, io, sys, csv
import pandas as pd
import boto3

def load_person_df(s3, bucket):
    key = "curated/person/person.csv"
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(io.BytesIO(obj["Body"].read()))
    # Expect columns: person_id, gender_concept_code, year_of_birth
    # Backwards compat: if birth_datetime exists instead of year_of_birth, coerce to year.
    if "year_of_birth" not in df.columns and "birth_datetime" in df.columns:
        df["year_of_birth"] = pd.to_datetime(df["birth_datetime"], errors="coerce").dt.year
    return df[["person_id", "gender_concept_code", "year_of_birth"]].dropna()

def try_kmeans(X, k):
    try:
        from sklearn.cluster import KMeans
        km = KMeans(n_clusters=k, n_init="auto", random_state=42)
        return km.fit_predict(X)
    except Exception:
        return None

def assign_fallback_buckets(df):
    # Simple “clusters” by age bucket
    # If year missing, set to median to avoid NaNs
    df = df.copy()
    yr = df["year_of_birth"].fillna(df["year_of_birth"].median())
    age = pd.Timestamp.utcnow().year - yr
    bins = pd.cut(age, bins=[-1, 40, 60, 200], labels=[0,1,2])  # 0: ≤40, 1: 41–60, 2: >60
    return bins.astype(int).values

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", required=True, help="S3 bucket that holds curated outputs (person/).")
    ap.add_argument("--k", type=int, default=3, help="Number of clusters")
    args = ap.parse_args()

    s3 = boto3.client("s3")
    df = load_person_df(s3, args.bucket)

    # One-hot gender (M/F/O/UNK) -> [M,F,O,UNK]
    genders = ["M","F","O","UNK"]
    gmap = {g:i for i,g in enumerate(genders)}
    g_idx = df["gender_concept_code"].map(lambda x: gmap.get(str(x).upper(), gmap["UNK"]))
    G = pd.get_dummies(g_idx).reindex(columns=range(len(genders)), fill_value=0)
    G.columns = [f"g_{g}" for g in genders]

    # Features: age proxy from year_of_birth (more stable than raw year)
    current_year = pd.Timestamp.utcnow().year
    age = (current_year - df["year_of_birth"]).fillna((current_year - df["year_of_birth"].median()))
    X = pd.concat([age.rename("age"), G.reset_index(drop=True)], axis=1)

    labels = try_kmeans(X.values, args.k)
    if labels is None:
        labels = assign_fallback_buckets(df)

    out = pd.DataFrame({
        "person_id": df["person_id"].astype(str).values,
        "cluster": labels
    })

    # Write to S3 (analytics path)
    out_key = "analytics/kmeans/assignments.csv"
    buf = io.StringIO()
    out.to_csv(buf, index=False)
    s3.put_object(Bucket=args.bucket, Key=out_key, Body=buf.getvalue().encode("utf-8"), ContentType="text/csv", ServerSideEncryption="AES256")
    print(f"Wrote s3://{args.bucket}/{out_key}")

    # Also save locally for GitHub
    os.makedirs("reports", exist_ok=True)
    local_path = "reports/cluster_assignments.csv"
    out.to_csv(local_path, index=False)
    print(f"Wrote {local_path}")

    # Tiny summary
    summary = out.groupby("cluster").size().reset_index(name="n").sort_values("cluster")
    print("\nCluster sizes:")
    print(summary.to_string(index=False))

if __name__ == "__main__":
    main()
