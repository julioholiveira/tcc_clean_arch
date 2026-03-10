#!/bin/bash

# Compara dois arquivos metrics_summary.json e gera um relatório consolidado.
# Uso:
#   ./scripts/compare_metrics.sh
#   ./scripts/compare_metrics.sh /caminho/baseline/metrics_summary.json /caminho/cleanarch/metrics_summary.json

set -euo pipefail

echo "==================================================="
echo "Comparando Métricas Baseline vs Clean Arch"
echo "==================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
METRICS_ROOT="$APP_ROOT/metrics"

find_latest_summary() {
    local prefix="$1"
    local latest_dir

    latest_dir=$(find "$METRICS_ROOT" -maxdepth 1 -type d -name "${prefix}_*" | sort | tail -n 1)
    if [ -z "$latest_dir" ]; then
        echo ""
        return
    fi

    echo "$latest_dir/metrics_summary.json"
}

BASELINE_SUMMARY="${1:-$(find_latest_summary baseline)}"
CLEANARCH_SUMMARY="${2:-$(find_latest_summary cleanarch)}"

if [ -z "$BASELINE_SUMMARY" ] || [ ! -f "$BASELINE_SUMMARY" ]; then
    echo "❌ Erro: arquivo baseline metrics_summary.json não encontrado"
    exit 1
fi

if [ -z "$CLEANARCH_SUMMARY" ] || [ ! -f "$CLEANARCH_SUMMARY" ]; then
    echo "❌ Erro: arquivo cleanarch metrics_summary.json não encontrado"
    exit 1
fi

RESULTS_DIR="$METRICS_ROOT/comparison_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "📥 Baseline: $BASELINE_SUMMARY"
echo "📥 Clean Arch: $CLEANARCH_SUMMARY"

BASELINE_SUMMARY="$BASELINE_SUMMARY" \
CLEANARCH_SUMMARY="$CLEANARCH_SUMMARY" \
RESULTS_DIR="$RESULTS_DIR" \
python3 <<'PYTHON'
import json
import os
from datetime import datetime
from pathlib import Path


baseline_path = Path(os.environ["BASELINE_SUMMARY"])
cleanarch_path = Path(os.environ["CLEANARCH_SUMMARY"])
results_dir = Path(os.environ["RESULTS_DIR"])


def load_json(path: Path):
    with path.open() as handle:
        return json.load(handle)


baseline = load_json(baseline_path)
cleanarch = load_json(cleanarch_path)


METRICS = [
    ("cc_average", "CC Média", "lower"),
    ("cc_maximum", "CC Máxima", "lower"),
    ("cc_grade_a_percent", "Grade A CC <= 5", "higher"),
    ("mi_average", "MI Médio", "higher"),
    ("mi_minimum", "MI Mínimo", "higher"),
]

COVERAGE_METRICS = [
    ("line_percent", "Line Coverage", "higher"),
    ("branch_percent", "Branch Coverage", "higher"),
]


def module_metric(summary, module_name, metric_key):
    module = summary["modules"][module_name]
    if metric_key == "cc_average":
        return module["cyclomatic_complexity"]["average"]
    if metric_key == "cc_maximum":
        return module["cyclomatic_complexity"]["maximum"]
    if metric_key == "cc_grade_a_percent":
        return module["cyclomatic_complexity"]["grade_a_percent"]
    if metric_key == "mi_average":
        return module["maintainability_index"]["average"]
    if metric_key == "mi_minimum":
        return module["maintainability_index"]["minimum"]
    raise KeyError(metric_key)


def fmt_number(value, is_percent=False):
    if value is None:
        return "N/A"
    return f"{value:.2f}%" if is_percent else f"{value:.2f}"


def pct_change(baseline_value, cleanarch_value):
    if baseline_value in (None, 0) or cleanarch_value is None:
        return None
    return ((cleanarch_value - baseline_value) / baseline_value) * 100


def interpretation(direction, baseline_value, cleanarch_value):
    if baseline_value is None or cleanarch_value is None:
        return "N/A"
    if cleanarch_value == baseline_value:
        return "estavel"
    if direction == "lower":
        return "melhorou" if cleanarch_value < baseline_value else "piorou"
    return "melhorou" if cleanarch_value > baseline_value else "piorou"


comparison = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "baseline_summary": str(baseline_path),
    "cleanarch_summary": str(cleanarch_path),
    "baseline_generated_at": baseline.get("generated_at"),
    "cleanarch_generated_at": cleanarch.get("generated_at"),
    "baseline_test_command": baseline.get("test_command"),
    "cleanarch_test_command": cleanarch.get("test_command"),
    "modules": {},
    "coverage": [],
}

table_rows = []

for module_name, module_label in (("core", "Core"), ("mailing", "Mailing")):
    rows = []
    for metric_key, metric_label, direction in METRICS:
        baseline_value = module_metric(baseline, module_name, metric_key)
        cleanarch_value = module_metric(cleanarch, module_name, metric_key)
        delta = None if baseline_value is None or cleanarch_value is None else cleanarch_value - baseline_value
        row = {
            "module": module_name,
            "metric": metric_key,
            "metric_label": metric_label,
            "baseline": baseline_value,
            "cleanarch": cleanarch_value,
            "delta": delta,
            "percent_change": pct_change(baseline_value, cleanarch_value),
            "direction": direction,
            "interpretation": interpretation(direction, baseline_value, cleanarch_value),
        }
        rows.append(row)
        table_rows.append(row)
    comparison["modules"][module_name] = rows

for metric_key, metric_label, direction in COVERAGE_METRICS:
    baseline_value = baseline["coverage"].get(metric_key)
    cleanarch_value = cleanarch["coverage"].get(metric_key)
    row = {
        "metric": metric_key,
        "metric_label": metric_label,
        "baseline": baseline_value,
        "cleanarch": cleanarch_value,
        "delta": None if baseline_value is None or cleanarch_value is None else cleanarch_value - baseline_value,
        "percent_change": pct_change(baseline_value, cleanarch_value),
        "direction": direction,
        "interpretation": interpretation(direction, baseline_value, cleanarch_value),
    }
    comparison["coverage"].append(row)
    table_rows.append({"module": "coverage", **row})


def row_to_markdown(category, label, baseline_value, cleanarch_value, delta, change, meaning, is_percent=False):
    delta_text = "N/A" if delta is None else (f"{delta:+.2f}%" if is_percent else f"{delta:+.2f}")
    change_text = "N/A" if change is None else f"{change:+.2f}%"
    return (
        f"| {category} | {label} | {fmt_number(baseline_value, is_percent)} | "
        f"{fmt_number(cleanarch_value, is_percent)} | {delta_text} | {change_text} | {meaning} |"
    )


md_lines = [
    "# Baseline vs Clean Arch Comparison",
    "",
    f"**Data:** {comparison['generated_at']}",
    f"**Baseline Summary:** {baseline_path}",
    f"**Clean Arch Summary:** {cleanarch_path}",
    f"**Baseline Executado em:** {comparison['baseline_generated_at']}",
    f"**Clean Arch Executado em:** {comparison['cleanarch_generated_at']}",
    "",
    "## Tabela Consolidada",
    "",
    "| Categoria | Métrica | Baseline | Clean Arch | Delta | Variação % | Leitura |",
    "|-----------|---------|----------|------------|-------|------------|---------|",
]

for row in table_rows:
    is_percent = row["metric"] in {"cc_grade_a_percent", "line_percent", "branch_percent"}
    category = "Coverage" if row["module"] == "coverage" else row["module"].capitalize()
    md_lines.append(
        row_to_markdown(
            category,
            row["metric_label"],
            row["baseline"],
            row["cleanarch"],
            row["delta"],
            row["percent_change"],
            row["interpretation"],
            is_percent=is_percent,
        )
    )

md_lines.extend(
    [
        "",
        "## Contexto",
        "",
        f"**Baseline Test Command:** {comparison['baseline_test_command']}",
        f"**Clean Arch Test Command:** {comparison['cleanarch_test_command']}",
        "",
        "## Observações",
        "",
        "- Para CC, valores menores são melhores.",
        "- Para MI, Grade A e cobertura, valores maiores são melhores.",
        "- O delta é calculado como `Clean Arch - Baseline`.",
    ]
)

(results_dir / "comparison_summary.md").write_text("\n".join(md_lines), encoding="utf-8")
(results_dir / "comparison_summary.json").write_text(json.dumps(comparison, indent=2, ensure_ascii=True), encoding="utf-8")
PYTHON

echo ""
echo "✅ Comparação gerada com sucesso!"
echo "📁 Resultados salvos em: $RESULTS_DIR"
echo "   - $RESULTS_DIR/comparison_summary.md"
echo "   - $RESULTS_DIR/comparison_summary.json"