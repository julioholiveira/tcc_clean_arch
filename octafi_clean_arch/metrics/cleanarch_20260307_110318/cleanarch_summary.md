# Clean Arch Metrics Report

**Data:** 2026-03-07 11:03:20
**Branch:** clean_arch
**Commit:** c814279
**Cenário:** cleanarch
**Alvo:** src/core, src/mailing (arquitetura limpa)

## 1. Complexidade Ciclomática (CC)

### Core Module (src/core)
**Média CC:** 2.30
**CC Máxima:** 10 (AuthenticateGuestUseCase.execute em src/core/application/use_cases/authenticate_guest.py:61)
**Total de funções/métodos:** 445
**Grade A (CC <= 5):** 427/445 (95.96%)

### Mailing Module (src/mailing)
**Média CC:** 2.59
**CC Máxima:** 11 (DjangoBulkSMSProcessor.process_bulk_send em src/mailing/infrastructure/bulk_sms_processor.py:28)
**Total de funções/métodos:** 224
**Grade A (CC <= 5):** 210/224 (93.75%)

## 2. Indice de Manutenibilidade (MI)

### Core Module (src/core)
**Média MI:** 79.72
**MI Minimo:** 29.35
**MI Maximo:** 100.00
**Pior arquivo por MI:** 29.35 (src/core/tests/domain/test_entities.py)

### Mailing Module (src/mailing)
**Média MI:** 79.68
**MI Minimo:** 23.47
**MI Maximo:** 100.00
**Pior arquivo por MI:** 23.47 (src/mailing/tests/domain/test_entities.py)

## 3. Cobertura de Testes

**Line Coverage:** 40.64%
**Branch Coverage:** 39.64%
**Total Lines:** 2069
**Lines Covered:** 843
**Total Branches:** 222
**Branches Covered:** 88
**Arquivos Medidos:** 89

## 4. Contexto da Execucao

**Coverage RCFile:** /Users/juliohenrique/work/octafi_clean_arch/octafi_clean_arch/.coveragerc.cleanarch
**Test Command:** pytest src/core/tests/ src/mailing/tests/ -v -p no:django --override-ini=addopts=
**Test Exit Code:** 0
