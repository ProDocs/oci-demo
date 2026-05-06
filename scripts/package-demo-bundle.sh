#!/usr/bin/env bash
set -euo pipefail

build_outcome="${1:-UNKNOWN}"
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "${project_root}/dist"
cp "${project_root}/ai-review.json" "${project_root}/dist/ai-review.json"

python3 - "${build_outcome}" "${project_root}" <<'PY'
import json
import sys
import zipfile
from pathlib import Path

build_outcome = sys.argv[1]
project_root = Path(sys.argv[2])
dist_dir = project_root / "dist"
target_dir = project_root / "target"
review_path = project_root / "ai-review.json"

review_payload = json.loads(review_path.read_text(encoding="utf-8"))
summary_path = dist_dir / "pipeline-summary.txt"
summary_lines = [
    f"build_outcome={build_outcome}",
    f"ai_review_result={review_payload.get('result', 'UNKNOWN')}",
    f"ai_review_comments={review_payload.get('comments', '')}",
]

native_binary = target_dir / "oci-ai-review-demo"
jar_file = target_dir / "oci-ai-review-demo.jar"
summary_lines.append(f"native_binary_present={'yes' if native_binary.exists() else 'no'}")
summary_lines.append(f"jar_present={'yes' if jar_file.exists() else 'no'}")

summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

bundle_path = dist_dir / "demo-bundle.zip"
with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zip_handle:
    zip_handle.write(dist_dir / "ai-review.json", arcname="ai-review.json")
    zip_handle.write(summary_path, arcname="pipeline-summary.txt")

    if jar_file.exists():
        zip_handle.write(jar_file, arcname=f"artifacts/{jar_file.name}")
    if native_binary.exists():
        zip_handle.write(native_binary, arcname=f"artifacts/{native_binary.name}")
PY
