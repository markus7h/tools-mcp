#!/usr/bin/env bash
# Duenner Wrapper: pipet tag_no_ocr.py in den paperless-ai-Container auf dem
# Docker-Host. Der Container bringt PAPERLESS_URL/PAPERLESS_TOKEN und httpx
# schon mit — so bleibt hier jede Secret-Behandlung aussen vor.
set -euo pipefail

: "${TOOLS_RUN_DIR:?TOOLS_RUN_DIR not set}"

HOST="${INPUT_HOST:-mystorage}"
CONTAINER="${INPUT_CONTAINER:-paperless-ai}"
TAG_NAME="${INPUT_TAG_NAME:-ohne OCR-Text}"
ARGS=""
[[ "${INPUT_APPLY:-false}" == "true" ]] && ARGS="--apply"

out="${TOOLS_RUN_DIR}/outputs.json"

ssh "$HOST" "docker exec -i -e TAG_NAME=\"$TAG_NAME\" $CONTAINER python - $ARGS" \
  < "$(dirname "$0")/tag_no_ocr.py" > "$out"

if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$out" 2>/dev/null; then
  printf 'ERROR: kein gueltiges JSON vom Container:\n%s\n' "$(cat "$out")" >&2
  rm -f "$out"
  exit 6
fi
cat "$out"
