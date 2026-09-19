curl --request POST \
  --url 'https://api.higgsfield.ai/marketing-studio/image' \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}" \
  --header "Content-Type: application/json" \
  --data @- <<'JSON'
{
  "prompt": "A cinematic scene at sunset",
  "quality": "high",
  "moderation": "auto",
  "resolution": "2k",
  "aspect_ratio": "16:9",
  "enhance_prompt": false
}
JSON
