#!/usr/bin/env bash
# Builds and deploys the Doculyze backend via AWS SAM.
set -euo pipefail

cd "$(dirname "$0")/../infra"

echo "==> Building SAM application"
sam build

echo "==> Deploying (guided — follow the prompts on first run)"
sam deploy --guided

echo ""
echo "Deploy complete. Copy the ApiEndpoint output above into frontend/.env"
echo "as VITE_API_BASE_URL, then run 'npm run build' in frontend/."
