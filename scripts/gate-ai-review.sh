#!/usr/bin/env bash
set -euo pipefail

review_file="${1:-ai-review.json}"

if [[ ! -f "${review_file}" ]]; then
  echo "Arquivo ${review_file} nao encontrado."
  exit 2
fi

result="$(
  python3 - "${review_file}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as file_handle:
    payload = json.load(file_handle)

print(payload.get("result", ""))
PY
)"

case "${result}" in
  PASS|WARN)
    echo "AI review liberou o build com resultado ${result}."
    ;;
  BLOCK)
    echo "AI review bloqueou o build antes da compilacao."
    cat "${review_file}"
    exit 1
    ;;
  *)
    echo "Resultado inesperado em ${review_file}: ${result}"
    exit 2
    ;;
esac

