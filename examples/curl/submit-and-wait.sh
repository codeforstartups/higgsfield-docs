#!/usr/bin/env bash
set -euo pipefail

: "${HF_API_KEY_ID:?Set HF_API_KEY_ID}"
: "${HF_API_KEY_SECRET:?Set HF_API_KEY_SECRET}"

API_BASE="${HF_API_BASE:-https://api.higgsfield.ai}"
MODEL_PATH="${1:-higgsfield-ai/soul/standard}"
INPUT_FILE="${2:-}"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required." >&2
  exit 1
fi

if [[ -n "${INPUT_FILE}" ]]; then
  payload="$(cat "${INPUT_FILE}")"
else
  payload='{"prompt":"Editorial portrait in soft daylight"}'
fi

response="$(
  curl --silent --show-error --fail-with-body \
    --request POST \
    --url "${API_BASE}/${MODEL_PATH}" \
    --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}" \
    --header "Content-Type: application/json" \
    --data "${payload}"
)"

echo "${response}" | jq
request_id="$(echo "${response}" | jq --exit-status --raw-output '.request_id')"
status_url="$(echo "${response}" | jq --raw-output '.status_url // empty')"
status_url="${status_url:-${API_BASE}/requests/${request_id}/status}"

delay=2
while true; do
  response="$(
    curl --silent --show-error --fail-with-body \
      --url "${status_url}" \
      --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}"
  )"
  status="$(echo "${response}" | jq --exit-status --raw-output '.status')"
  echo "Request ${request_id}: ${status}" >&2

  case "${status}" in
    completed)
      echo "${response}" | jq
      exit 0
      ;;
    failed | nsfw | canceled)
      echo "${response}" | jq
      exit 1
      ;;
    queued | in_progress)
      sleep "${delay}"
      ((delay = delay < 30 ? delay * 2 : 30))
      ;;
    *)
      echo "Unknown status: ${status}" >&2
      echo "${response}" | jq
      exit 1
      ;;
  esac
done
