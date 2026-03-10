# Baseline vs Clean Arch Comparison

**Data:** 2026-03-07 11:05:59
**Baseline Summary:** /Users/juliohenrique/work/octafi_clean_arch/octafi_clean_arch/metrics/baseline_20260307_110527/metrics_summary.json
**Clean Arch Summary:** /Users/juliohenrique/work/octafi_clean_arch/octafi_clean_arch/metrics/cleanarch_20260307_110318/metrics_summary.json
**Baseline Executado em:** 2026-03-07 11:05:37
**Clean Arch Executado em:** 2026-03-07 11:03:20

## Tabela Consolidada

| Categoria | Métrica | Baseline | Clean Arch | Delta | Variação % | Leitura |
|-----------|---------|----------|------------|-------|------------|---------|
| Core | CC Média | 1.72 | 2.30 | +0.59 | +34.09% | piorou |
| Core | CC Máxima | 15.00 | 10.00 | -5.00 | -33.33% | melhorou |
| Core | Grade A CC <= 5 | 95.16% | 95.96% | +0.79% | +0.83% | melhorou |
| Core | MI Médio | 93.94 | 79.72 | -14.22 | -15.14% | piorou |
| Core | MI Mínimo | 37.07 | 29.35 | -7.71 | -20.81% | piorou |
| Mailing | CC Média | 1.53 | 2.59 | +1.06 | +69.10% | piorou |
| Mailing | CC Máxima | 6.00 | 11.00 | +5.00 | +83.33% | piorou |
| Mailing | Grade A CC <= 5 | 96.88% | 93.75% | -3.12% | -3.23% | piorou |
| Mailing | MI Médio | 98.29 | 79.68 | -18.61 | -18.93% | piorou |
| Mailing | MI Mínimo | 52.08 | 23.47 | -28.61 | -54.93% | piorou |
| Coverage | Line Coverage | 57.77% | 40.64% | -17.14% | -29.66% | piorou |
| Coverage | Branch Coverage | 32.19% | 39.64% | +7.45% | +23.14% | melhorou |

## Contexto

**Baseline Test Command:** python manage.py test core.tests mailing --verbosity 2
**Clean Arch Test Command:** pytest src/core/tests/ src/mailing/tests/ -v -p no:django --override-ini=addopts=

## Observações

- Para CC, valores menores são melhores.
- Para MI, Grade A e cobertura, valores maiores são melhores.
- O delta é calculado como `Clean Arch - Baseline`.