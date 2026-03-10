#!/bin/bash

# Script para coleta de métricas do código legado (core e mailing na raiz).
# Coleta CC, MI e coverage com o mesmo formato usado no cenário clean architecture.

set -euo pipefail

echo "==================================================="
echo "Coletando Métricas Baseline - Octafi Clean Arch"
echo "==================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck disable=SC1091
source "$SCRIPT_DIR/common_metrics.sh"

export SECRET_KEY="${SECRET_KEY:-metrics-secret-key}"
export DEBUG="${DEBUG:-False}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///$WORKSPACE_ROOT/db.sqlite3}"
export ALLOWED_HOSTS="${ALLOWED_HOSTS:-127.0.0.1}"
export CSRF_TRUSTED_ORIGINS="${CSRF_TRUSTED_ORIGINS:-}"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://localhost:6379/0}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-redis://localhost:6379/1}"
export SENDGRID_API_KEY="${SENDGRID_API_KEY:-dummy-sendgrid-key}"
export RECAPTCHA_SITE_KEY="${RECAPTCHA_SITE_KEY:-dummy-site-key}"
export RECAPTCHA_SECRET_KEY="${RECAPTCHA_SECRET_KEY:-dummy-secret-key}"
export SAFE_LIST_IPS="${SAFE_LIST_IPS:-127.0.0.1}"

EXECUTION_ROOT="$WORKSPACE_ROOT"
VENV_ROOT="$APP_ROOT"
RESULTS_DIR="$APP_ROOT/metrics/baseline_$(date +%Y%m%d_%H%M%S)"
REPORT_TITLE="Baseline Metrics Report"
SUMMARY_FILENAME="baseline_summary.md"
TARGET_DESCRIPTION="core, mailing (legado)"
CORE_PATH="core"
MAILING_PATH="mailing"
CORE_LABEL="Core Module (legacy core/)"
MAILING_LABEL="Mailing Module (legacy mailing/)"
COVERAGE_RCFILE="$APP_ROOT/.coveragerc"
SCENARIO_NAME="baseline"
TEST_RUNNER_MODE="script"
TEST_RUNNER="manage.py"
TEST_RUNNER_ARGS=(test core.tests mailing --verbosity 2)
TEST_COMMAND_DISPLAY="python manage.py test core.tests mailing --verbosity 2"

run_metrics_collection

echo ""
echo "==================================================="
echo "✅ Baseline coletado com sucesso!"
echo "📁 Resultados salvos em: $RESULTS_DIR"
echo "==================================================="
echo ""
echo "Próximos passos:"
echo "1. Revisar $RESULTS_DIR/$SUMMARY_FILENAME"
echo "2. Comparar com metrics/cleanarch_*/metrics_summary.json"
echo "3. Executar: make baseline-performance (testes de carga)"