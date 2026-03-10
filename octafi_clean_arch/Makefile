.PHONY: help \
	baseline-metrics baseline-docker baseline-performance baseline-all clean-baseline \
	install-deps verify \
	cleanarch-up cleanarch-down cleanarch-metrics cleanarch-radon cleanarch-coverage cleanarch-perf cleanarch-all \
	compare-metrics

help:
	@echo "Comandos disponíveis:"
	@echo ""
	@echo "── Ambiente ──────────────────────────────────────────────────────────"
	@echo "  make verify                - Verifica se o ambiente está pronto"
	@echo "  make install-deps          - Instala dependências para coleta de métricas"
	@echo ""
	@echo "── Baseline (legado) ─────────────────────────────────────────────────"
	@echo "  make baseline-all          - Executa baseline completo (métricas + Docker + performance)"
	@echo "  make baseline-metrics      - Coleta métricas de código (CC, MI, Coverage)"
	@echo "  make baseline-docker       - Inicia ambiente Docker controlado (porta 8001)"
	@echo "  make baseline-performance  - Executa testes de carga com Locust (baseline)"
	@echo "  make clean-baseline        - Remove containers e dados de baseline"
	@echo ""
	@echo "── Clean Arch (nova estrutura) ───────────────────────────────────────"
	@echo "  make cleanarch-all         - Executa métricas + Docker + performance (clean arch)"
	@echo "  make cleanarch-up          - Inicia ambiente Docker clean arch (porta 8002)"
	@echo "  make cleanarch-down        - Para e remove containers clean arch"
	@echo "  make cleanarch-metrics     - Coleta CC, MI e Coverage de src/core e src/mailing"
	@echo "  make cleanarch-radon       - Executa apenas Radon CC + MI"
	@echo "  make cleanarch-coverage    - Executa apenas Coverage --branch"
	@echo "  make cleanarch-perf        - Executa testes de carga Locust v1 (porta 8002)"
	@echo "  make compare-metrics       - Compara o último baseline com o último clean arch"

install-deps:
	@echo "Instalando dependências para coleta de métricas..."
	pip install radon coverage pytest pytest-cov locust

verify:
	@echo "Verificando ambiente..."
	@bash scripts/verify_setup.sh

baseline-metrics:
	@echo "Coletando métricas baseline..."
	@bash scripts/baseline_metrics.sh

baseline-docker:
	@echo "Iniciando ambiente Docker controlado..."
	@if [ ! -f "Dockerfile.dev" ]; then \
		echo "⚠️  Dockerfile.dev não encontrado. Usando Dockerfile padrão..."; \
		cp Dockerfile.prod Dockerfile.dev 2>/dev/null || echo "Aviso: Dockerfile não encontrado"; \
	fi
	docker-compose -f docker/docker-compose.baseline.yml up -d --build
	@echo "Aguardando serviços ficarem prontos (30s)..."
	@sleep 30
	@echo "Executando migrações..."
	docker-compose -f docker/docker-compose.baseline.yml exec -T web_baseline python manage.py migrate --noinput || true
	@echo "✅ Ambiente pronto! Aplicação disponível em http://localhost:8001"

baseline-performance:
	@echo "Executando testes de performance..."
	@bash scripts/run_performance_baseline.sh

baseline-all: baseline-metrics baseline-docker baseline-performance
	@echo ""
	@echo "==================================================="
	@echo "✅ Baseline completo executado!"
	@echo "==================================================="
	@echo ""
	@echo "Relatórios disponíveis em:"
	@echo "  - metrics/baseline_*/"
	@echo "  - metrics/performance_baseline_*/"
	@echo ""

clean-baseline:
	@echo "Removendo containers e dados de baseline..."
	docker-compose -f docker/docker-compose.baseline.yml down -v
	@echo "✅ Ambiente limpo!"

# Comandos adicionais úteis
logs-baseline:
	docker-compose -f docker/docker-compose.baseline.yml logs -f

status-baseline:
	docker-compose -f docker/docker-compose.baseline.yml ps

# ── Clean Arch targets ────────────────────────────────────────────────────────

cleanarch-up:
	@echo "Iniciando ambiente Docker clean arch (porta 8002)..."
	docker-compose -f docker/docker-compose.cleanarch.yml up -d --build
	@echo "Aguardando serviços ficarem prontos (30s)..."
	@sleep 30
	@echo "Executando migrações..."
	docker-compose -f docker/docker-compose.cleanarch.yml exec -T web_cleanarch python manage.py migrate --noinput || true
	@echo "✅ Ambiente pronto! Aplicação disponível em http://localhost:8002"

cleanarch-down:
	@echo "Removendo containers e dados clean arch..."
	docker-compose -f docker/docker-compose.cleanarch.yml down -v
	@echo "✅ Ambiente limpo!"

cleanarch-metrics:
	@echo "Coletando métricas clean arch (src/core, src/mailing)..."
	@bash scripts/cleanarch_metrics.sh

cleanarch-radon:
	@echo "Radon CC + MI sobre src/core e src/mailing..."
	@cd "$(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))" && \
		radon cc src/core src/mailing -a -s && \
		echo "" && \
		radon mi src/core src/mailing -s

cleanarch-coverage:
	@echo "Coverage --branch sobre src/core e src/mailing..."
	@cd "$(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))" && \
		coverage run --rcfile=.coveragerc.cleanarch \
			-m pytest src/core/tests/ src/mailing/tests/ -v \
			-p no:django --override-ini="addopts=" && \
		coverage report --rcfile=.coveragerc.cleanarch && \
		coverage html --rcfile=.coveragerc.cleanarch -d htmlcov_cleanarch

cleanarch-perf:
	@echo "Executando testes de performance clean arch (Locust v1)..."
	@bash scripts/run_performance_cleanarch.sh

cleanarch-all: cleanarch-metrics cleanarch-up cleanarch-perf
	@echo ""
	@echo "==================================================="
	@echo "✅ Medições clean arch completas!"
	@echo "==================================================="
	@echo ""
	@echo "Relatórios disponíveis em:"
	@echo "  - metrics/cleanarch_*/"
	@echo "  - metrics/performance_cleanarch_*/"
	@echo ""

compare-metrics:
	@echo "Comparando último baseline com último clean arch..."
	@bash scripts/compare_metrics.sh

logs-cleanarch:
	docker-compose -f docker/docker-compose.cleanarch.yml logs -f

status-cleanarch:
	docker-compose -f docker/docker-compose.cleanarch.yml ps
