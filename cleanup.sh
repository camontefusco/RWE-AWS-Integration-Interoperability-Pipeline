#!/usr/bin/env bash
set -euo pipefail
: "${BUCKET:?Set BUCKET env var}"
# Danger: empties curated/fhir/athena-results/analytics
aws s3 rm "s3://$BUCKET/curated/" --recursive || true
aws s3 rm "s3://$BUCKET/fhir/" --recursive || true
aws s3 rm "s3://$BUCKET/athena-results/" --recursive || true
aws s3 rm "s3://$BUCKET/analytics/" --recursive || true
echo "Optionally: npx serverless remove --stage dev --param='bucket=$BUCKET'"
