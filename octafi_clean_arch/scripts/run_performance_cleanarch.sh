#!/bin/bash

# Script para executar testes de performance da arquitetura limpa com Locust
# Aponta para http://localhost:8002 (docker-compose.cleanarch.yml)
# Usa locustfile_core_v1.py e locustfile_mailing_v1.py

set -e

echo "==================================================="
echo "Testes de Performance Clean Arch - Locust"
echo "==================================================="

# Resolver caminhos
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEANARCH_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"  # octafi_clean_arch/
cd "$CLEANARCH_ROOT"

RESULTS_DIR="metrics/performance_cleanarch_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# Verificar se aplicação está rodando em 8002
echo "🔍 Verificando se aplicação clean arch está disponível em localhost:8002..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002 || echo "000")
if ! echo "$HTTP_CODE" | grep -qE "^(200|302|404|403)$"; then
    echo "❌ Aplicação não está respondendo em localhost:8002 (código: $HTTP_CODE)"
    echo "Execute: make cleanarch-up"
    exit 1
fi
echo "✅ Aplicação disponível (HTTP $HTTP_CODE)"
echo ""

# Verificar locustfiles
if [ ! -f "load_tests/locustfile_core_v1.py" ]; then
    echo "❌ load_tests/locustfile_core_v1.py não encontrado"
    exit 1
fi
if [ ! -f "load_tests/locustfile_mailing_v1.py" ]; then
    echo "❌ load_tests/locustfile_mailing_v1.py não encontrado"
    exit 1
fi

# Configurações de teste — idênticas ao baseline para comparação justa
USERS=100
SPAWN_RATE=5
RUN_TIME="5m"

echo "📊 Configuração dos testes:"
echo "  Usuários simultâneos: $USERS"
echo "  Taxa de spawn: $SPAWN_RATE/s"
echo "  Duração: $RUN_TIME"
echo "  Host: http://localhost:8002"
echo ""

# ── 1. Teste Core v1 ───────────────────────────────────────────────────────────
echo "🔥 1. Testando módulo Core v1 (/api/v1/guest/*, /api/v1/sms/*)..."
locust \
    -f load_tests/locustfile_core_v1.py \
    --headless \
    --users $USERS \
    --spawn-rate $SPAWN_RATE \
    --run-time $RUN_TIME \
    --host http://localhost:8002 \
    --html "$RESULTS_DIR/locust_core_report.html" \
    --csv "$RESULTS_DIR/locust_core" \
    2>&1 | tee "$RESULTS_DIR/locust_core_output.log"

echo "✅ Teste Core v1 concluído"
echo ""

# Cooldown entre testes
echo "⏳ Aguardando 30s de cooldown..."
sleep 30

# ── 2. Teste Mailing v1 ────────────────────────────────────────────────────────
echo "🔥 2. Testando módulo Mailing v1 (/api/v1/mailing/campaigns/*)..."
locust \
    -f load_tests/locustfile_mailing_v1.py \
    --headless \
    --users $USERS \
    --spawn-rate $SPAWN_RATE \
    --run-time $RUN_TIME \
    --host http://localhost:8002 \
    --html "$RESULTS_DIR/locust_mailing_report.html" \
    --csv "$RESULTS_DIR/locust_mailing" \
    2>&1 | tee "$RESULTS_DIR/locust_mailing_output.log"

echo "✅ Teste Mailing v1 concluído"
echo ""

# ── 3. Gerar sumário ────────────────────────────────────────────────────────────
echo "📝 Gerando sumário de performance..."

# Substituir $RESULTS_DIR antes de executar Python para evitar o bug do heredoc com aspas simples
SUMMARY_SCRIPT=$(mktemp /tmp/perf_summary_XXXXXX.py)
cat > "$SUMMARY_SCRIPT" << PYEOF
import csv
import json
from pathlib import Path
from datetime import datetime

results_dir = Path("${RESULTS_DIR}")

print("# Performance Clean Arch Report")
print()
print(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"**Host:** http://localhost:8002")
print(f"**Usuários:** {USERS}")
print(f"**Spawn Rate:** {SPAWN_RATE}/s")
print(f"**Duração:** {RUN_TIME}")
print()

for module in ['core', 'mailing']:
    print(f"## {module.capitalize()} Module (v1)")
    print()

    stats_file = results_dir / f"locust_{module}_stats.csv"
    if stats_file.exists():
        with open(stats_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        data_rows = [r for r in rows if r.get('Type') != 'None' and r.get('Name')]
        if data_rows:
            print("| Endpoint | Requests | Failures | Avg (ms) | p50 (ms) | p95 (ms) | p99 (ms) | RPS |")
            print("|----------|----------|----------|----------|----------|----------|----------|-----|")
            for row in data_rows:
                failures = int(row.get('Failure Count', 0))
                failure_cell = f"**{failures}** ⚠️" if failures > 0 else str(failures)
                print(
                    f"| {row['Name']} | {row['Request Count']} | {failure_cell} | "
                    f"{row.get('Average Response Time','-')} | {row.get('50%','-')} | "
                    f"{row.get('95%','-')} | {row.get('99%','-')} | "
                    f"{row.get('Requests/s','-')} |"
                )
            print()
        else:
            print("Nenhum dado disponível.")
            print()
    else:
        print(f"Arquivo não encontrado: {stats_file}")
        print()

print("## Observações")
print()
print("- Valores em milissegundos (ms)")
print("- RPS = Requisições por segundo")
print("- p50, p95, p99 = percentis de latência")
print("- Comparar com metrics/performance_baseline_*/ para avaliar delta")
print()
PYEOF

python3 "$SUMMARY_SCRIPT" > "$RESULTS_DIR/performance_summary.md"
rm -f "$SUMMARY_SCRIPT"

echo "✅ Sumário gerado em $RESULTS_DIR/performance_summary.md"

echo ""
echo "==================================================="
echo "✅ Testes de performance clean arch concluídos!"
echo "📁 Resultados salvos em: $RESULTS_DIR"
echo "==================================================="
echo ""
echo "Visualize os relatórios HTML:"
echo "  - $RESULTS_DIR/locust_core_report.html"
echo "  - $RESULTS_DIR/locust_mailing_report.html"
echo ""
echo "Compare com o baseline:"
echo "  - metrics/performance_baseline_*/"
echo ""
