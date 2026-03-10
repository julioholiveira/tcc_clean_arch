#!/bin/bash

# Script de verificação - confirma que o ambiente está pronto

echo "=========================================="
echo "Verificação do Ambiente - Octafi Clean Arch"
echo "=========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
WARNINGS=0
ERRORS=0

# Função para verificar comando
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 está instalado ($(command -v $1))"
        ((SUCCESS++))
        return 0
    else
        echo -e "${RED}✗${NC} $1 não está instalado"
        ((ERRORS++))
        return 1
    fi
}

# Função para verificar arquivo
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 existe"
        ((SUCCESS++))
        return 0
    else
        echo -e "${RED}✗${NC} $1 não encontrado"
        ((ERRORS++))
        return 1
    fi
}

# Função para verificar diretório
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} Diretório $1 existe"
        ((SUCCESS++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Diretório $1 não encontrado"
        ((WARNINGS++))
        return 1
    fi
}

echo "1. Verificando comandos necessários..."
echo "--------------------------------------"
check_command python3
check_command pip
check_command docker
check_command docker-compose
check_command git
echo ""

echo "2. Verificando dependências Python..."
echo "--------------------------------------"
check_command radon || echo "   Instale com: pip install radon"
check_command coverage || echo "   Instale com: pip install coverage"
check_command pytest || echo "   Instale com: pip install pytest"
check_command locust || echo "   Instale com: pip install locust"
echo ""

echo "3. Verificando estrutura de arquivos..."
echo "--------------------------------------"
check_file "Makefile"
check_file ".coveragerc"
check_file "pytest.ini"
check_file "README.md"
check_file ".gitignore"
echo ""

echo "4. Verificando scripts..."
echo "--------------------------------------"
check_file "scripts/baseline_metrics.sh"
check_file "scripts/run_performance_baseline.sh"
check_file "scripts/README.md"
echo ""

echo "5. Verificando testes de carga..."
echo "--------------------------------------"
check_file "load_tests/locustfile_core.py"
check_file "load_tests/locustfile_mailing.py"
check_file "load_tests/README.md"
echo ""

echo "6. Verificando Docker..."
echo "--------------------------------------"
check_file "docker/docker-compose.baseline.yml"
echo ""

echo "7. Verificando documentação..."
echo "--------------------------------------"
check_file "docs/STEP1_BASELINE.md"
check_file "docs/STEP1_CHECKLIST.md"
check_file "docs/architecture/baseline_corrected.md"
echo ""

echo "8. Verificando estrutura src/..."
echo "--------------------------------------"
check_dir "src"
check_dir "src/core"
check_dir "src/mailing"
echo ""

echo "9. Verificando permissões de scripts..."
echo "--------------------------------------"
if [ -x "scripts/baseline_metrics.sh" ]; then
    echo -e "${GREEN}✓${NC} baseline_metrics.sh é executável"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠${NC} baseline_metrics.sh não é executável"
    echo "   Execute: chmod +x scripts/baseline_metrics.sh"
    ((WARNINGS++))
fi

if [ -x "scripts/run_performance_baseline.sh" ]; then
    echo -e "${GREEN}✓${NC} run_performance_baseline.sh é executável"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠${NC} run_performance_baseline.sh não é executável"
    echo "   Execute: chmod +x scripts/run_performance_baseline.sh"
    ((WARNINGS++))
fi
echo ""

# Verificar Docker daemon
echo "10. Verificando Docker daemon..."
echo "--------------------------------------"
if docker info &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker daemon está rodando"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC} Docker daemon não está rodando"
    echo "   Inicie o Docker Desktop/daemon"
    ((ERRORS++))
fi
echo ""

# Resumo
echo "=========================================="
echo "Resumo da Verificação"
echo "=========================================="
echo -e "${GREEN}Sucessos: $SUCCESS${NC}"
echo -e "${YELLOW}Avisos: $WARNINGS${NC}"
echo -e "${RED}Erros: $ERRORS${NC}"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Ambiente está pronto!${NC}"
    echo ""
    echo "Próximos passos:"
    echo "  1. Execute: make baseline-all"
    echo "  2. Revise: docs/STEP1_BASELINE.md"
    echo "  3. Siga o checklist: docs/STEP1_CHECKLIST.md"
    exit 0
else
    echo -e "${RED}✗ Há erros que precisam ser corrigidos${NC}"
    echo ""
    echo "Para instalar dependências: make install-deps"
    echo "Para mais informações: cat README.md"
    exit 1
fi
