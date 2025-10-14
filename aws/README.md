# Lambda (ingestTransform)
Deploy:
  npx serverless deploy --stage dev --param='bucket=YOUR_BUCKET'
Verify:
  aws s3api get-bucket-notification-configuration --bucket YOUR_BUCKET
Env:
  BUCKET, CURATED_PREFIX=curated/, FHIR_PREFIX=fhir/, PSEUD_ID_SALT
