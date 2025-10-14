# Architecture
S3 (raw) -> Lambda (ingestTransform) -> S3 (curated, fhir) -> Athena (DDL) -> reports/
Optional: openFDA external table, KMeans (local NumPy), QuickSight/Grafana later.
