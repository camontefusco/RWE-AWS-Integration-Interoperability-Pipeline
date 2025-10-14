#!/usr/bin/env bash
set -euo pipefail
: "${BUCKET:?Set BUCKET env var}"
TS=$(date +%s)
aws s3 cp samples/sample_rwd.csv "s3://$BUCKET/raw/sample_rwd_$TS.csv"

# Optional: (re)apply DDLs if you include them in sql/ddl/
# aws athena start-query-execution --work-group primary \
#   --result-configuration OutputLocation="s3://$BUCKET/athena-results/" \
#   --query-string "$(cat sql/ddl/01_create_db_and_tables.sql)" >/dev/null

# Athena visuals (CSV + HTML)
./refresh_dashboard.sh

echo "Open locally: reports/openfda_dashboard.html"
