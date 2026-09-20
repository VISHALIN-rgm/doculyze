#!/usr/bin/env bash
# Uploads every file in docs/sample-documents/ straight to the S3 uploads
# bucket and starts the explain workflow for each — useful for testing
# the pipeline without going through the frontend.
#
# Usage: ./seed_test_data.sh <bucket-name> <state-machine-arn>

set -euo pipefail

BUCKET="${1:?Usage: seed_test_data.sh <bucket-name> <state-machine-arn>}"
STATE_MACHINE_ARN="${2:?Usage: seed_test_data.sh <bucket-name> <state-machine-arn>}"
SAMPLES_DIR="$(dirname "$0")/../docs/sample-documents"

shopt -s nullglob
files=("$SAMPLES_DIR"/*.pdf "$SAMPLES_DIR"/*.png "$SAMPLES_DIR"/*.jpg "$SAMPLES_DIR"/*.jpeg)

if [ ${#files[@]} -eq 0 ]; then
  echo "No sample documents found in $SAMPLES_DIR — add a few files first."
  exit 1
fi

for file in "${files[@]}"; do
  name="$(basename "$file")"
  doc_id="$(uuidgen | tr -d '-' | head -c 32)"
  key="uploads/${doc_id}/${name}"

  echo "==> Uploading ${name} as ${doc_id}"
  aws s3 cp "$file" "s3://${BUCKET}/${key}"

  aws stepfunctions start-execution \
    --state-machine-arn "$STATE_MACHINE_ARN" \
    --input "{\"documentId\":\"${doc_id}\",\"bucket\":\"${BUCKET}\",\"key\":\"${key}\",\"documentName\":\"${name}\"}" \
    > /dev/null

  echo "    started workflow for documentId=${doc_id}"
done
