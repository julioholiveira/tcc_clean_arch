# Load Tests - Locust

Testes de carga para medição de performance baseline e comparação pós-refatoração.

## Arquivos

### locustfile_core.py

Testa o módulo **Core** (autenticação guest WiFi):

**Cenários simulados:**

- `GuestAuthUser`: Usuário se autenticando na rede WiFi
  - GET landing page
  - POST autenticação com telefone
  - POST verificação de código SMS
  - GET página pré-login
- `SMSStatusUser`: Verificação de status de SMS
  - GET status de SMS via API

**Endpoints testados:**

- `/landingpage/mac={mac}&site_id={site}&campanha_id=None&empresa={id}`
- `/landingpage_passcode/`
- `/landingpage_guest_pre/{site}`
- `/api/sms/status/`

### locustfile_mailing.py

Testa o módulo **Mailing** (campanhas de SMS):

**Cenários simulados:**

- `MailingUser`: Usuário gerenciando campanhas
  - GET lista de campanhas
  - GET seleção de destinatários (com filtros de data)
  - GET/POST envio de campanha

**Endpoints testados:**

- `/mailing/lista_mailings/`
- `/mailing/selecionar_destinatarios/{id}`
- `/mailing/enviar_mailing/{id}`

## Como Usar

### 1. Via Make (Recomendado)

```bash
# Iniciar ambiente Docker primeiro
make baseline-docker

# Executar testes de performance
make baseline-performance
```

### 2. Manualmente com Locust

**Interface Web (modo interativo):**

```bash
locust -f load_tests/locustfile_core.py --host http://localhost:8001
# Acesse http://localhost:8089 no navegador
```

**Headless (automático):**

```bash
locust -f load_tests/locustfile_core.py \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --host http://localhost:8001 \
  --html results/report.html
```

## Configuração

### Parâmetros Padrão

- **Usuários simultâneos**: 50
- **Spawn rate**: 5 usuários/segundo
- **Duração**: 5 minutos
- **Host**: http://localhost:8001

### Customização

Edite `scripts/run_performance_baseline.sh` para ajustar:

```bash
USERS=50           # Número de usuários simulados
SPAWN_RATE=5       # Taxa de criação de usuários (por segundo)
RUN_TIME="5m"      # Duração do teste (5m, 10m, 1h, etc)
```

## Métricas Coletadas

- **Latência média** (Average Response Time)
- **Percentis**: p50, p95, p99
- **Throughput**: Requisições por segundo (RPS)
- **Taxa de falha**: % de requisições que falharam
- **Número total de requisições**
- **Usuários simultâneos**

## Resultados

Os resultados são salvos em `metrics/performance_baseline_YYYYMMDD_HHMMSS/`:

```
performance_baseline_YYYYMMDD_HHMMSS/
├── locust_core_report.html       # Relatório HTML interativo (Core)
├── locust_core_stats.csv          # Estatísticas detalhadas (Core)
├── locust_core_failures.csv       # Falhas detalhadas (Core)
├── locust_core_output.log         # Log de execução (Core)
├── locust_mailing_report.html     # Relatório HTML interativo (Mailing)
├── locust_mailing_stats.csv       # Estatísticas detalhadas (Mailing)
├── locust_mailing_failures.csv    # Falhas detalhadas (Mailing)
├── locust_mailing_output.log      # Log de execução (Mailing)
└── performance_summary.md         # Sumário consolidado
```

## Interpretação dos Resultados

### Latência

- **p50 (mediana)**: metade das requisições são mais rápidas que este valor
- **p95**: 95% das requisições são mais rápidas que este valor
- **p99**: 99% das requisições são mais rápidas que este valor

### Benchmarks Esperados (baseline)

| Módulo  | Endpoint                           | p95 esperado | RPS esperado |
| ------- | ---------------------------------- | ------------ | ------------ |
| Core    | /landingpage/                      | <500ms       | >10          |
| Core    | /landingpage_passcode/             | <300ms       | >15          |
| Mailing | /mailing/lista_mailings/           | <400ms       | >12          |
| Mailing | /mailing/selecionar_destinatarios/ | <800ms       | >8           |

_Valores indicativos - ajustar após primeira medição_

## Troubleshooting

**Erro: Connection refused**

```bash
# Verificar se aplicação está rodando
curl http://localhost:8001
# ou
make status-baseline
```

**Erro: Too many 500 errors**

```bash
# Verificar logs da aplicação
make logs-baseline

# Pode ser necessário ajustar número de usuários
# Edite USERS no script run_performance_baseline.sh
```

**Resultados inconsistentes**

- Execute múltiplas vezes e compare
- Certifique-se que nada mais está rodando no sistema
- Use ambiente Docker para isolamento

## Boas Práticas

1. **Sempre execute em ambiente controlado** (Docker)
2. **Execute múltiplas vezes** para validar consistência
3. **Documente diferenças de hardware** entre medições
4. **Use os mesmos parâmetros** para comparações antes/depois
5. **Aguarde cooldown** entre testes (30s padrão)

## Referências

- [Documentação Locust](https://docs.locust.io/)
- [Best Practices for Load Testing](https://docs.locust.io/en/stable/writing-a-locustfile.html)
