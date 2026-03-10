#!/bin/bash

# Script para executar testes de performance baseline com Locust

set -e

echo "==================================================="
echo "Testes de Performance Baseline - Locust"
echo "==================================================="

RESULTS_DIR="metrics/performance_baseline_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# Verificar se aplicação está rodando
echo "🔍 Verificando se aplicação está disponível..."
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:8001 | grep -q "200\|302\|404"; then
    echo "❌ Aplicação não está rodando em localhost:8001"
    echo "Execute: make baseline-docker"
    exit 1
fi

echo "✅ Aplicação disponível"
echo ""

# Configurações de teste
USERS=100
SPAWN_RATE=5
RUN_TIME="5m"

echo "📊 Executando testes de carga..."
echo "Usuários simultâneos: $USERS"
echo "Taxa de spawn: $SPAWN_RATE/s"
echo "Duração: $RUN_TIME"
echo ""

# Teste Core
echo "🔥 1. Testando módulo Core..."
locust \
    -f load_tests/locustfile_core.py \
    --headless \
    --users $USERS \
    --spawn-rate $SPAWN_RATE \
    --run-time $RUN_TIME \
    --host http://localhost:8001 \
    --html "$RESULTS_DIR/locust_core_report.html" \
    --csv "$RESULTS_DIR/locust_core" \
    2>&1 | tee "$RESULTS_DIR/locust_core_output.log"

echo "✅ Teste Core concluído"
echo ""

# Aguardar cooldown
echo "⏳ Aguardando 30s de cooldown..."
sleep 30

# Teste Mailing
echo "🔥 2. Testando módulo Mailing..."
locust \
    -f load_tests/locustfile_mailing.py \
    --headless \
    --users $USERS \
    --spawn-rate $SPAWN_RATE \
    --run-time $RUN_TIME \
    --host http://localhost:8001 \
    --html "$RESULTS_DIR/locust_mailing_report.html" \
    --csv "$RESULTS_DIR/locust_mailing" \
    2>&1 | tee "$RESULTS_DIR/locust_mailing_output.log"

echo "✅ Teste Mailing concluído"
echo ""

# Gerar sumário
echo "📝 Gerando sumário de performance..."

python3 << 'PYTHON' > "$RESULTS_DIR/performance_summary.md"
import csv
import json
from pathlib import Path
from datetime import datetime

print("# Performance Baseline Report")
print()
print(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"**Usuários:** 100")
print(f"**Spawn Rate:** 5/s")
print(f"**Duração:** 5m")
print()

for module in ['core', 'mailing']:
    print(f"## {module.capitalize()} Module")
    print()
    
    stats_file = Path(f"$RESULTS_DIR/locust_{module}_stats.csv")
    if stats_file.exists():
        with open(stats_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if rows:
                print("| Endpoint | Requests | Failures | Avg (ms) | p50 (ms) | p95 (ms) | p99 (ms) | RPS |")
                print("|----------|----------|----------|----------|----------|----------|----------|-----|")
                
                for row in rows:
                    if row['Type'] == 'None' or not row['Name']:
                        continue
                    print(f"| {row['Name']} | {row['Request Count']} | {row['Failure Count']} | "
                          f"{row['Average Response Time']} | {row['50%']} | {row['95%']} | "
                          f"{row['99%']} | {row['Requests/s']} |")
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
print()
PYTHON

echo "✅ Sumário gerado em $RESULTS_DIR/performance_summary.md"

echo ""
echo "==================================================="
echo "✅ Testes de performance concluídos!"
echo "📁 Resultados salvos em: $RESULTS_DIR"
echo "==================================================="
echo ""
echo "Visualize os relatórios HTML:"
echo "  - $RESULTS_DIR/locust_core_report.html"
echo "  - $RESULTS_DIR/locust_mailing_report.html"
echo ""
