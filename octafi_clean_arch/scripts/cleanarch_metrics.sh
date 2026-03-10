#!/bin/bash

# Script para coleta de métricas da arquitetura limpa (src/core e src/mailing).
# Coleta CC, MI e coverage com o mesmo formato usado no cenário legado.

set -euo pipefail

echo "==================================================="
echo "Coletando Métricas Clean Arch - Octafi"
echo "==================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ ! -d "$APP_ROOT/src/core" ] || [ ! -d "$APP_ROOT/src/mailing" ]; then
    echo "❌ Erro: src/core ou src/mailing não encontrado em $APP_ROOT"
    exit 1
fi

# shellcheck disable=SC1091
source "$SCRIPT_DIR/common_metrics.sh"

EXECUTION_ROOT="$APP_ROOT"
VENV_ROOT="$APP_ROOT"
RESULTS_DIR="$APP_ROOT/metrics/cleanarch_$(date +%Y%m%d_%H%M%S)"
REPORT_TITLE="Clean Arch Metrics Report"
SUMMARY_FILENAME="cleanarch_summary.md"
TARGET_DESCRIPTION="src/core, src/mailing (arquitetura limpa)"
CORE_PATH="src/core"
MAILING_PATH="src/mailing"
CORE_LABEL="Core Module (src/core)"
MAILING_LABEL="Mailing Module (src/mailing)"
COVERAGE_RCFILE="$APP_ROOT/.coveragerc.cleanarch"
SCENARIO_NAME="cleanarch"
TEST_RUNNER_MODE="module"
TEST_RUNNER="pytest"
TEST_RUNNER_ARGS=(src/core/tests/ src/mailing/tests/ -v -p no:django --override-ini=addopts=)
TEST_COMMAND_DISPLAY="pytest src/core/tests/ src/mailing/tests/ -v -p no:django --override-ini=addopts="

run_metrics_collection

echo ""
echo "==================================================="
echo "✅ Métricas clean arch coletadas com sucesso!"
echo "📁 Resultados salvos em: $RESULTS_DIR"
echo "==================================================="
echo ""
echo "Próximos passos:"
echo "1. Revisar $RESULTS_DIR/$SUMMARY_FILENAME"
echo "2. Comparar com metrics/baseline_*/metrics_summary.json"
echo "3. Executar: make cleanarch-perf (testes de carga)"
echo ""