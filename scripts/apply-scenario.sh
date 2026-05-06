#!/usr/bin/env bash
set -euo pipefail

scenario="${1:-}"
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

controller_target="${project_root}/src/main/java/com/example/ociaidemo/controller/GreetingController.java"
service_target="${project_root}/src/main/java/com/example/ociaidemo/service/GreetingService.java"

copy_pass_baseline() {
  cp "${project_root}/examples/scenarios/pass/GreetingController.java" "${controller_target}"
  cp "${project_root}/examples/scenarios/pass/GreetingService.java" "${service_target}"
}

case "${scenario}" in
  pass)
    copy_pass_baseline
    ;;
  warn)
    copy_pass_baseline
    cp "${project_root}/examples/scenarios/warn/GreetingService.java" "${service_target}"
    ;;
  block)
    copy_pass_baseline
    cp "${project_root}/examples/scenarios/block/GreetingController.java" "${controller_target}"
    ;;
  *)
    cat <<'EOF'
Uso: bash scripts/apply-scenario.sh <pass|warn|block>

pass  - restaura o baseline aderente
warn  - aplica o service com TODO/FIXME
block - aplica o controller que acessa repository diretamente
EOF
    exit 1
    ;;
esac

echo "Scenario aplicado: ${scenario}"
