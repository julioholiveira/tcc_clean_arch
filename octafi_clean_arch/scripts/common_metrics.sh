#!/bin/bash

require_metrics_variables() {
    local required_vars=(
        EXECUTION_ROOT
        VENV_ROOT
        RESULTS_DIR
        REPORT_TITLE
        SUMMARY_FILENAME
        TARGET_DESCRIPTION
        CORE_PATH
        MAILING_PATH
        CORE_LABEL
        MAILING_LABEL
        COVERAGE_RCFILE
        SCENARIO_NAME
        TEST_COMMAND_DISPLAY
        TEST_RUNNER_MODE
        TEST_RUNNER
    )

    local missing=0
    for var_name in "${required_vars[@]}"; do
        if [ -z "${!var_name:-}" ]; then
            echo "❌ Erro: variável obrigatória não definida: $var_name"
            missing=1
        fi
    done

    if [ "$missing" -ne 0 ]; then
        exit 1
    fi

    if [ "${#TEST_RUNNER_ARGS[@]}" -eq 0 ]; then
        echo "❌ Erro: TEST_RUNNER_ARGS não foi configurado"
        exit 1
    fi
}

activate_metrics_environment() {
    echo "🐍 Ativando ambiente virtual..."

    if [ -n "${VIRTUAL_ENV:-}" ]; then
        echo "✅ Ambiente virtual já ativo: $VIRTUAL_ENV"
        echo ""
        return
    fi

    if [ -f "$VENV_ROOT/.venv/bin/activate" ]; then
        # shellcheck disable=SC1091
        source "$VENV_ROOT/.venv/bin/activate"
        echo "✅ Ambiente '.venv' ativado"
        echo ""
        return
    fi

    if command -v pyenv >/dev/null 2>&1; then
        eval "$(pyenv init -)"
        if pyenv commands | grep -qx "virtualenv-init"; then
            eval "$(pyenv virtualenv-init -)"
        fi

        if pyenv activate octafi >/dev/null 2>&1; then
            echo "✅ Ambiente 'octafi' ativado via pyenv"
            echo ""
            return
        fi
    fi

    echo "❌ Erro: nenhum ambiente virtual disponível"
    echo "Esperado: ambiente já ativo, $VENV_ROOT/.venv, ou pyenv com virtualenv 'octafi'"
    exit 1
}

check_metrics_dependencies() {
    local dependencies=(radon coverage pytest python3)

    for dependency in "${dependencies[@]}"; do
        if ! command -v "$dependency" >/dev/null 2>&1; then
            echo "❌ Erro: dependência não encontrada: $dependency"
            echo "Execute: pip install radon coverage pytest pytest-cov"
            exit 1
        fi
    done
}

collect_cc_metrics() {
    local module_path="$1"
    local module_slug="$2"
    local module_label="$3"

    if [ ! -d "$EXECUTION_ROOT/$module_path" ]; then
        echo "❌ Erro: diretório não encontrado: $EXECUTION_ROOT/$module_path"
        exit 1
    fi

    echo "$module_label:"
    (
        cd "$EXECUTION_ROOT"
        radon cc "$module_path/" -a -s -j > "$RESULTS_DIR/radon_cc_${module_slug}.json"
        radon cc "$module_path/" -a -s > "$RESULTS_DIR/radon_cc_${module_slug}.txt"
    )
}

collect_mi_metrics() {
    local module_path="$1"
    local module_slug="$2"
    local module_label="$3"

    if [ ! -d "$EXECUTION_ROOT/$module_path" ]; then
        echo "❌ Erro: diretório não encontrado: $EXECUTION_ROOT/$module_path"
        exit 1
    fi

    echo "$module_label:"
    (
        cd "$EXECUTION_ROOT"
        radon mi "$module_path/" -s -j > "$RESULTS_DIR/radon_mi_${module_slug}.json"
        radon mi "$module_path/" -s > "$RESULTS_DIR/radon_mi_${module_slug}.txt"
    )
}

run_coverage_metrics() {
    local test_exit_code
    local previous_dir="$PWD"

    cd "$EXECUTION_ROOT"
    coverage erase --rcfile="$COVERAGE_RCFILE"

    set +e
    if [ "$TEST_RUNNER_MODE" = "module" ]; then
        coverage run --rcfile="$COVERAGE_RCFILE" -m "$TEST_RUNNER" "${TEST_RUNNER_ARGS[@]}"
    else
        coverage run --rcfile="$COVERAGE_RCFILE" "$TEST_RUNNER" "${TEST_RUNNER_ARGS[@]}"
    fi
    test_exit_code=$?
    set -e

    coverage report --rcfile="$COVERAGE_RCFILE" > "$RESULTS_DIR/coverage_report.txt"
    coverage json --rcfile="$COVERAGE_RCFILE" -o "$RESULTS_DIR/coverage.json"
    coverage html --rcfile="$COVERAGE_RCFILE" -d "$RESULTS_DIR/htmlcov"

    cd "$previous_dir"

    printf '%s' "$test_exit_code" > "$RESULTS_DIR/test_exit_code.txt"

    if [ "$test_exit_code" -ne 0 ]; then
        echo "⚠️  Aviso: o comando de testes encerrou com código $test_exit_code. Os relatórios foram gerados com os dados disponíveis."
    fi
}

generate_metrics_outputs() {
    RESULTS_DIR="$RESULTS_DIR" \
    REPORT_TITLE="$REPORT_TITLE" \
    SUMMARY_FILENAME="$SUMMARY_FILENAME" \
    TARGET_DESCRIPTION="$TARGET_DESCRIPTION" \
    CORE_LABEL="$CORE_LABEL" \
    MAILING_LABEL="$MAILING_LABEL" \
    COVERAGE_RCFILE="$COVERAGE_RCFILE" \
    SCENARIO_NAME="$SCENARIO_NAME" \
    TEST_COMMAND_DISPLAY="$TEST_COMMAND_DISPLAY" \
    python3 <<'PYTHON'
import json
import os
from datetime import datetime
from pathlib import Path


results_dir = Path(os.environ["RESULTS_DIR"])
summary_path = results_dir / os.environ["SUMMARY_FILENAME"]
summary_json_path = results_dir / "metrics_summary.json"


def load_json(path: Path):
    if not path.exists():
        return {}
    with path.open() as handle:
        return json.load(handle)


def cc_stats(module_slug: str):
    data = load_json(results_dir / f"radon_cc_{module_slug}.json")
    entries = []
    for file_path, blocks in data.items():
        for block in blocks:
            enriched = dict(block)
            enriched["_file"] = file_path
            entries.append(enriched)

    if not entries:
        return {
            "average": None,
            "maximum": None,
            "total_blocks": 0,
            "grade_a_count": 0,
            "grade_a_percent": None,
            "worst_block": None,
        }

    worst = max(entries, key=lambda item: item.get("complexity", 0))
    grade_a_count = sum(1 for item in entries if item.get("rank") == "A")
    return {
        "average": sum(item.get("complexity", 0) for item in entries) / len(entries),
        "maximum": max(item.get("complexity", 0) for item in entries),
        "total_blocks": len(entries),
        "grade_a_count": grade_a_count,
        "grade_a_percent": (grade_a_count / len(entries)) * 100,
        "worst_block": {
            "file": worst.get("_file"),
            "line": worst.get("lineno"),
            "name": worst.get("name"),
            "class": worst.get("classname"),
            "complexity": worst.get("complexity"),
        },
    }


def mi_stats(module_slug: str):
    data = load_json(results_dir / f"radon_mi_{module_slug}.json")
    entries = []
    for file_path, file_data in data.items():
        enriched = dict(file_data)
        enriched["_file"] = file_path
        entries.append(enriched)

    if not entries:
        return {
            "average": None,
            "minimum": None,
            "maximum": None,
            "worst_file": None,
        }

    scores = [entry.get("mi", 0) for entry in entries]
    worst = min(entries, key=lambda item: item.get("mi", 0))
    return {
        "average": sum(scores) / len(scores),
        "minimum": min(scores),
        "maximum": max(scores),
        "worst_file": {
            "file": worst.get("_file"),
            "mi": worst.get("mi"),
            "rank": worst.get("rank"),
        },
    }


coverage_data = load_json(results_dir / "coverage.json")
coverage_totals = coverage_data.get("totals", {})
test_exit_code_path = results_dir / "test_exit_code.txt"
test_exit_code = test_exit_code_path.read_text().strip() if test_exit_code_path.exists() else "unknown"

summary = {
    "report_title": os.environ["REPORT_TITLE"],
    "scenario": os.environ["SCENARIO_NAME"],
    "target": os.environ["TARGET_DESCRIPTION"],
    "coverage_rcfile": os.environ["COVERAGE_RCFILE"],
    "test_command": os.environ["TEST_COMMAND_DISPLAY"],
    "test_exit_code": int(test_exit_code) if test_exit_code.isdigit() else test_exit_code,
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "modules": {
        "core": {
            "label": os.environ["CORE_LABEL"],
            "cyclomatic_complexity": cc_stats("core"),
            "maintainability_index": mi_stats("core"),
        },
        "mailing": {
            "label": os.environ["MAILING_LABEL"],
            "cyclomatic_complexity": cc_stats("mailing"),
            "maintainability_index": mi_stats("mailing"),
        },
    },
    "coverage": {
        "line_percent": coverage_totals.get("percent_covered"),
        "branch_percent": (
            (coverage_totals.get("covered_branches", 0) / coverage_totals.get("num_branches", 1)) * 100
            if coverage_totals.get("num_branches", 0)
            else None
        ),
        "total_lines": coverage_totals.get("num_statements"),
        "covered_lines": coverage_totals.get("covered_lines"),
        "total_branches": coverage_totals.get("num_branches"),
        "covered_branches": coverage_totals.get("covered_branches"),
        "measured_files": len(coverage_data.get("files", {})),
    },
}


def fmt_float(value):
    return f"{value:.2f}" if isinstance(value, (int, float)) else "N/A"


def fmt_percent(value):
    return f"{value:.2f}%" if isinstance(value, (int, float)) else "N/A"


def fmt_worst_cc(worst_block):
    if not worst_block:
        return "N/A"
    class_name = worst_block.get("class")
    qualified_name = worst_block.get("name")
    if class_name:
        qualified_name = f"{class_name}.{qualified_name}"
    return f"{worst_block.get('complexity')} ({qualified_name} em {worst_block.get('file')}:{worst_block.get('line')})"


def fmt_worst_mi(worst_file):
    if not worst_file:
        return "N/A"
    return f"{worst_file.get('mi'):.2f} ({worst_file.get('file')})"


lines = [
    f"# {summary['report_title']}",
    "",
    f"**Data:** {summary['generated_at']}",
    f"**Branch:** {os.popen('git branch --show-current 2>/dev/null || echo unknown').read().strip()}",
    f"**Commit:** {os.popen('git rev-parse --short HEAD 2>/dev/null || echo unknown').read().strip()}",
    f"**Cenário:** {summary['scenario']}",
    f"**Alvo:** {summary['target']}",
    "",
    "## 1. Complexidade Ciclomática (CC)",
    "",
]

for module_name in ("core", "mailing"):
    module_summary = summary["modules"][module_name]
    cc_summary = module_summary["cyclomatic_complexity"]
    lines.extend(
        [
            f"### {module_summary['label']}",
            f"**Média CC:** {fmt_float(cc_summary['average'])}",
            f"**CC Máxima:** {fmt_worst_cc(cc_summary['worst_block'])}",
            f"**Total de funções/métodos:** {cc_summary['total_blocks']}",
            (
                f"**Grade A (CC <= 5):** {cc_summary['grade_a_count']}/{cc_summary['total_blocks']} "
                f"({fmt_percent(cc_summary['grade_a_percent'])})"
                if cc_summary['total_blocks']
                else "**Grade A (CC <= 5):** N/A"
            ),
            "",
        ]
    )

lines.extend(["## 2. Indice de Manutenibilidade (MI)", ""])

for module_name in ("core", "mailing"):
    module_summary = summary["modules"][module_name]
    mi_summary = module_summary["maintainability_index"]
    lines.extend(
        [
            f"### {module_summary['label']}",
            f"**Média MI:** {fmt_float(mi_summary['average'])}",
            f"**MI Minimo:** {fmt_float(mi_summary['minimum'])}",
            f"**MI Maximo:** {fmt_float(mi_summary['maximum'])}",
            f"**Pior arquivo por MI:** {fmt_worst_mi(mi_summary['worst_file'])}",
            "",
        ]
    )

coverage_summary = summary["coverage"]
lines.extend(
    [
        "## 3. Cobertura de Testes",
        "",
        f"**Line Coverage:** {fmt_percent(coverage_summary['line_percent'])}",
        f"**Branch Coverage:** {fmt_percent(coverage_summary['branch_percent'])}",
        f"**Total Lines:** {coverage_summary['total_lines'] if coverage_summary['total_lines'] is not None else 'N/A'}",
        f"**Lines Covered:** {coverage_summary['covered_lines'] if coverage_summary['covered_lines'] is not None else 'N/A'}",
        f"**Total Branches:** {coverage_summary['total_branches'] if coverage_summary['total_branches'] is not None else 'N/A'}",
        f"**Branches Covered:** {coverage_summary['covered_branches'] if coverage_summary['covered_branches'] is not None else 'N/A'}",
        f"**Arquivos Medidos:** {coverage_summary['measured_files']}",
        "",
        "## 4. Contexto da Execucao",
        "",
        f"**Coverage RCFile:** {summary['coverage_rcfile']}",
        f"**Test Command:** {summary['test_command']}",
        f"**Test Exit Code:** {summary['test_exit_code']}",
        "",
    ]
)

summary_path.write_text("\n".join(lines), encoding="utf-8")
summary_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8")
PYTHON
}

run_metrics_collection() {
    require_metrics_variables
    mkdir -p "$RESULTS_DIR"

    activate_metrics_environment
    check_metrics_dependencies

    echo ""
    echo "📊 1. Analisando Complexidade Ciclomática (Radon CC)..."
    echo "---------------------------------------------------"
    collect_cc_metrics "$CORE_PATH" "core" "$CORE_LABEL"
    collect_cc_metrics "$MAILING_PATH" "mailing" "$MAILING_LABEL"
    echo "✅ Complexidade Ciclomática coletada"

    echo ""
    echo "📈 2. Analisando Índice de Manutenibilidade (Radon MI)..."
    echo "---------------------------------------------------"
    collect_mi_metrics "$CORE_PATH" "core" "$CORE_LABEL"
    collect_mi_metrics "$MAILING_PATH" "mailing" "$MAILING_LABEL"
    echo "✅ Índice de Manutenibilidade coletado"

    echo ""
    echo "🧪 3. Executando Testes com Coverage (--branch)..."
    echo "---------------------------------------------------"
    run_coverage_metrics
    echo "✅ Coverage coletado (line + branch)"

    echo ""
    echo "📝 4. Gerando Sumário de Métricas..."
    echo "---------------------------------------------------"
    generate_metrics_outputs
    echo "✅ Sumário gerado em $RESULTS_DIR/$SUMMARY_FILENAME"
    echo "✅ Sumário estruturado gerado em $RESULTS_DIR/metrics_summary.json"
}