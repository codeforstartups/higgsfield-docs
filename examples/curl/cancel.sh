#!/usr/bin/env bash
set -euo pipefail

: "${HF_API_KEY_ID:?Set HF_API_KEY_ID}"
: "${HF_API_KEY_SECRET:?Set HF_API_KEY_SECRET}"
: "${1:?Usage: ./cancel.sh REQUEST_ID}"

API_BASE="${HF_API_BASE:-https://api.higgsfield.ai}"

curl --silent --show-error --fail-with-body \
  --request POST \
  --url "${API_BASE}/requests/${1}/cancel" \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}"

echo "Cancellation accepted for ${1}."
