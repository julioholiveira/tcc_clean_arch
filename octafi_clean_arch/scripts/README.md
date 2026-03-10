# Scripts de Baseline

Este diretório contém scripts para coleta de métricas baseline antes da refatoração.

## Scripts Disponíveis

### baseline_metrics.sh

Coleta métricas de código estático:

- **Radon CC**: Complexidade Ciclomática
- **Radon MI**: Índice de Manutenibilidade
- **Coverage**: Cobertura de testes (line e branch)
- **Summary JSON**: Resumo estruturado para comparação com clean arch

No legado, a etapa de testes usa o runner Django via `manage.py test`; no clean arch, usa `pytest`.

**Uso:**

```bash
./scripts/baseline_metrics.sh
# ou
make baseline-metrics
```

**Saída:**

- `metrics/baseline_YYYYMMDD_HHMMSS/` - diretório com todos os relatórios
- Arquivos JSON e TXT com métricas detalhadas
- `baseline_summary.md` - sumário consolidado
- `metrics_summary.json` - sumário estruturado com o mesmo schema do clean arch

### cleanarch_metrics.sh

Coleta o mesmo conjunto de métricas do baseline no código novo em `src/core` e `src/mailing`:

- **Radon CC**: Complexidade Ciclomática
- **Radon MI**: Índice de Manutenibilidade
- **Coverage**: Cobertura de testes (line e branch)
- **Summary JSON**: Resumo estruturado para comparação com baseline

**Uso:**

```bash
./scripts/cleanarch_metrics.sh
# ou
make cleanarch-metrics
```

**Saída:**

- `metrics/cleanarch_YYYYMMDD_HHMMSS/` - diretório com todos os relatórios
- Arquivos JSON e TXT com métricas detalhadas
- `cleanarch_summary.md` - sumário consolidado
- `metrics_summary.json` - sumário estruturado com o mesmo schema do baseline

### compare_metrics.sh

Compara dois arquivos `metrics_summary.json` e gera um delta consolidado entre baseline e clean architecture.

Se executado sem argumentos, usa automaticamente o último `metrics/baseline_*/metrics_summary.json` e o último `metrics/cleanarch_*/metrics_summary.json`.

**Uso:**

```bash
./scripts/compare_metrics.sh
# ou
make compare-metrics

# comparação explícita
./scripts/compare_metrics.sh \
    metrics/baseline_YYYYMMDD_HHMMSS/metrics_summary.json \
    metrics/cleanarch_YYYYMMDD_HHMMSS/metrics_summary.json
```

**Saída:**

- `metrics/comparison_YYYYMMDD_HHMMSS/` - diretório com os relatórios comparativos
- `comparison_summary.md` - tabela consolidada baseline vs clean arch
- `comparison_summary.json` - delta estruturado para automação

### run_performance_baseline.sh

Executa testes de carga com Locust:

- Simula 50 usuários simultâneos
- Testa módulos Core e Mailing
- Coleta métricas de latência (média, p50, p95, p99)
- Mede throughput (requisições/segundo)

**Pré-requisitos:**

- Aplicação rodando em http://localhost:8001
- Execute primeiro: `make baseline-docker`

**Uso:**

```bash
./scripts/run_performance_baseline.sh
# ou
make baseline-performance
```

**Saída:**

- `metrics/performance_baseline_YYYYMMDD_HHMMSS/` - diretório com relatórios
- Arquivos HTML interativos do Locust
- CSVs com estatísticas detalhadas
- `performance_summary.md` - sumário consolidado

## Dependências

Instale as dependências necessárias:

```bash
make install-deps
# ou
pip install radon coverage pytest pytest-cov locust
```

## Workflow Completo

Execute todo o baseline de uma vez:

```bash
make baseline-all
```

Isso irá:

1. Coletar métricas de código
2. Iniciar ambiente Docker controlado
3. Executar testes de performance
4. Gerar todos os relatórios

## Resultados

Todos os resultados são salvos em `metrics/` com timestamp:

```
metrics/
├── baseline_YYYYMMDD_HHMMSS/
│   ├── radon_cc_*.json
│   ├── radon_mi_*.json
│   ├── coverage.json
│   ├── htmlcov/
│   ├── baseline_summary.md
│   └── metrics_summary.json
├── cleanarch_YYYYMMDD_HHMMSS/
│   ├── radon_cc_*.json
│   ├── radon_mi_*.json
│   ├── coverage.json
│   ├── htmlcov/
│   ├── cleanarch_summary.md
│   └── metrics_summary.json
├── comparison_YYYYMMDD_HHMMSS/
│   ├── comparison_summary.md
│   └── comparison_summary.json
└── performance_baseline_YYYYMMDD_HHMMSS/
    ├── locust_*_report.html
    ├── locust_*_stats.csv
    └── performance_summary.md
```

## Troubleshooting

**Erro: "radon: command not found"**

```bash
make install-deps
```

**Erro: "Application not running on localhost:8001"**

```bash
make baseline-docker
```

**Erro: Docker containers não iniciam**

```bash
# Verificar logs
make logs-baseline

# Limpar e tentar novamente
make clean-baseline
make baseline-docker
```
