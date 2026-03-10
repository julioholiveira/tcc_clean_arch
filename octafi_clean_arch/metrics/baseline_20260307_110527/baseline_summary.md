# Baseline Metrics Report

**Data:** 2026-03-07 11:05:37
**Branch:** clean_arch
**Commit:** c814279
**Cenário:** baseline
**Alvo:** core, mailing (legado)

## 1. Complexidade Ciclomática (CC)

### Core Module (legacy core/)
**Média CC:** 1.72
**CC Máxima:** 15 (landingpage_guest em core/views.py:144)
**Total de funções/métodos:** 124
**Grade A (CC <= 5):** 118/124 (95.16%)

### Mailing Module (legacy mailing/)
**Média CC:** 1.53
**CC Máxima:** 6 (selecionar_destinatarios em mailing/views.py:98)
**Total de funções/métodos:** 32
**Grade A (CC <= 5):** 31/32 (96.88%)

## 2. Indice de Manutenibilidade (MI)

### Core Module (legacy core/)
**Média MI:** 93.94
**MI Minimo:** 37.07
**MI Maximo:** 100.00
**Pior arquivo por MI:** 37.07 (core/views.py)

### Mailing Module (legacy mailing/)
**Média MI:** 98.29
**MI Minimo:** 52.08
**MI Maximo:** 100.00
**Pior arquivo por MI:** 52.08 (mailing/views.py)

## 3. Cobertura de Testes

**Line Coverage:** 57.77%
**Branch Coverage:** 32.19%
**Total Lines:** 600
**Lines Covered:** 384
**Total Branches:** 146
**Branches Covered:** 47
**Arquivos Medidos:** 17

## 4. Contexto da Execucao

**Coverage RCFile:** /Users/juliohenrique/work/octafi_clean_arch/octafi_clean_arch/.coveragerc
**Test Command:** python manage.py test core.tests mailing --verbosity 2
**Test Exit Code:** 0
