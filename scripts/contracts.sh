#!/bin/bash
# Снятие снапшотов OpenAPI со всех поднятых сервисов.
#
# Снапшоты коммитятся: расхождение файла с кодом должно быть видно в диффе,
# а не всплывать у потребителя контракта (packages/contracts/README.md).
set -euo pipefail

OUT="packages/contracts/openapi"
mkdir -p "$OUT"

declare -A PORTS=(
    [plan-service]=8001
    [site-service]=8002
    [analysis-service]=8003
    [vision-service]=8004
    [report-service]=8005
    [pos-engine]=8000
)
declare -A PREFIX=(
    [plan-service]=plan
    [site-service]=site
    [analysis-service]=analysis
    [vision-service]=vision
    [report-service]=report
    [pos-engine]=pos
)

taken=0
for service in "${!PORTS[@]}"; do
    url="http://localhost:${PORTS[$service]}/api/v1/${PREFIX[$service]}/openapi.json"
    if curl -fsS -m 5 "$url" -o "$OUT/$service.json" 2>/dev/null; then
        python3 -m json.tool "$OUT/$service.json" > "$OUT/$service.json.tmp"
        mv "$OUT/$service.json.tmp" "$OUT/$service.json"
        echo "снят: $service"
        taken=$((taken + 1))
    else
        echo "пропущен: $service (не поднят)"
    fi
done

echo
echo "снято снапшотов: $taken"
[ "$taken" -eq 0 ] && { echo "Ни один сервис не отвечает. Сначала make up."; exit 1; }

# TS-клиент генерируется из этих же снапшотов, когда появится apps/web.
[ -d apps/web/node_modules ] && echo "TS-клиент: генерация появится вместе с apps/web"
exit 0
