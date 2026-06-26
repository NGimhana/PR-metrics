#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"

work_dir="${WORK_DIR:-$repo_root/checkout-bugs-final}"

input_jsons=(
	"${repo_root}/hunk4j/dataset/claude/LocalNoTests/d4j_dataset_final.json"
    "${repo_root}/hunk4j/dataset/claude/LocalTests/d4j_dataset_final.json"
    "${repo_root}/hunk4j/dataset/claude/NonLocalNoTests/d4j_dataset_final.json"
    "${repo_root}/hunk4j/dataset/claude/NonLocalTests/d4j_dataset_final.json"

    "${repo_root}/hunk4j/dataset/codex/LocalNoTests/d4j_dataset_final.json"
    "${repo_root}/hunk4j/dataset/codex/LocalTests/d4j_dataset_final.json"
    "${repo_root}/hunk4j/dataset/codex/NonLocalNoTests/d4j_dataset_final.json"
    "${repo_root}/hunk4j/dataset/codex/NonLocalTests/d4j_dataset_final.json"
    
    "${repo_root}/hunk4j/dataset/gemini/LocalNoTests/d4j_dataset_final.json"
    "${repo_root}/hunk4j/dataset/gemini/LocalTests/d4j_dataset_final.json"
    "${repo_root}/hunk4j/dataset/gemini/NonLocalNoTests/d4j_dataset_final.json"
    "${repo_root}/hunk4j/dataset/gemini/NonLocalTests/d4j_dataset_final.json"
)

patches_dirs=(
	"${repo_root}/patches/claude/LocalNoTests"
    "${repo_root}/patches/claude/LocalTests"
    "${repo_root}/patches/claude/NonLocalNoTests"
    "${repo_root}/patches/claude/NonLocalTests"

    "${repo_root}/patches/codex/LocalNoTests"
    "${repo_root}/patches/codex/LocalTests"
    "${repo_root}/patches/codex/NonLocalNoTests"
    "${repo_root}/patches/codex/NonLocalTests"
    
    "${repo_root}/patches/gemini/LocalNoTests"
    "${repo_root}/patches/gemini/LocalTests"
    "${repo_root}/patches/gemini/NonLocalNoTests"
    "${repo_root}/patches/gemini/NonLocalTests"
)

ast_jsons=(
	"${repo_root}/hunk4j/javaparser/method-line-extractor/claude/LocalNoTests/AST_ast.json"
    "${repo_root}/hunk4j/javaparser/method-line-extractor/claude/LocalTests/AST_ast.json"
    "${repo_root}/hunk4j/javaparser/method-line-extractor/claude/NonLocalNoTests/AST_ast.json"
    "${repo_root}/hunk4j/javaparser/method-line-extractor/claude/NonLocalTests/AST_ast.json"

    "${repo_root}/hunk4j/javaparser/method-line-extractor/codex/LocalNoTests/AST_ast.json"
    "${repo_root}/hunk4j/javaparser/method-line-extractor/codex/LocalTests/AST_ast.json"
    "${repo_root}/hunk4j/javaparser/method-line-extractor/codex/NonLocalNoTests/AST_ast.json"
    "${repo_root}/hunk4j/javaparser/method-line-extractor/codex/NonLocalTests/AST_ast.json"
    
    "${repo_root}/hunk4j/javaparser/method-line-extractor/gemini/LocalNoTests/AST_ast.json"
    "${repo_root}/hunk4j/javaparser/method-line-extractor/gemini/LocalTests/AST_ast.json"
    "${repo_root}/hunk4j/javaparser/method-line-extractor/gemini/NonLocalNoTests/AST_ast.json"
    "${repo_root}/hunk4j/javaparser/method-line-extractor/gemini/NonLocalTests/AST_ast.json"
)

output_csvs=(
	"${script_dir}/claude/LocalNoTests/total_hunk_divergence.csv"
    "${script_dir}/claude/LocalTests/total_hunk_divergence.csv"
    "${script_dir}/claude/NonLocalNoTests/total_hunk_divergence.csv"
    "${script_dir}/claude/NonLocalTests/total_hunk_divergence.csv"

    "${script_dir}/codex/LocalNoTests/total_hunk_divergence.csv"
    "${script_dir}/codex/LocalTests/total_hunk_divergence.csv"
    "${script_dir}/codex/NonLocalNoTests/total_hunk_divergence.csv"
    "${script_dir}/codex/NonLocalTests/total_hunk_divergence.csv"
    
    "${script_dir}/gemini/LocalNoTests/total_hunk_divergence.csv"
    "${script_dir}/gemini/LocalTests/total_hunk_divergence.csv"
    "${script_dir}/gemini/NonLocalNoTests/total_hunk_divergence.csv"
    "${script_dir}/gemini/NonLocalTests/total_hunk_divergence.csv"
)

pairwise_csvs=(
	"${script_dir}/claude/LocalNoTests/pairwise_hunk_divergence.csv"
    "${script_dir}/claude/LocalTests/pairwise_hunk_divergence.csv"
    "${script_dir}/claude/NonLocalNoTests/pairwise_hunk_divergence.csv"
    "${script_dir}/claude/NonLocalTests/pairwise_hunk_divergence.csv"

    "${script_dir}/codex/LocalNoTests/pairwise_hunk_divergence.csv"
    "${script_dir}/codex/LocalTests/pairwise_hunk_divergence.csv"
    "${script_dir}/codex/NonLocalNoTests/pairwise_hunk_divergence.csv"
    "${script_dir}/codex/NonLocalTests/pairwise_hunk_divergence.csv"
    
    "${script_dir}/gemini/LocalNoTests/pairwise_hunk_divergence.csv"
    "${script_dir}/gemini/LocalTests/pairwise_hunk_divergence.csv"
    "${script_dir}/gemini/NonLocalNoTests/pairwise_hunk_divergence.csv"
    "${script_dir}/gemini/NonLocalTests/pairwise_hunk_divergence.csv"
)

bugwise_csvs=(
	"${script_dir}/claude/LocalNoTests/bugwise_average_divergence.csv"
    "${script_dir}/claude/LocalTests/bugwise_average_divergence.csv"
    "${script_dir}/claude/NonLocalNoTests/bugwise_average_divergence.csv"
    "${script_dir}/claude/NonLocalTests/bugwise_average_divergence.csv"

    "${script_dir}/codex/LocalNoTests/bugwise_average_divergence.csv"
    "${script_dir}/codex/LocalTests/bugwise_average_divergence.csv"
    "${script_dir}/codex/NonLocalNoTests/bugwise_average_divergence.csv"
    "${script_dir}/codex/NonLocalTests/bugwise_average_divergence.csv"
    
    "${script_dir}/gemini/LocalNoTests/bugwise_average_divergence.csv"
    "${script_dir}/gemini/LocalTests/bugwise_average_divergence.csv"
    "${script_dir}/gemini/NonLocalNoTests/bugwise_average_divergence.csv"
    "${script_dir}/gemini/NonLocalTests/bugwise_average_divergence.csv"
)

# Validate arrays have same lengths
if [[ ${#input_jsons[@]} -ne ${#patches_dirs[@]} || ${#input_jsons[@]} -ne ${#ast_jsons[@]} || ${#input_jsons[@]} -ne ${#output_csvs[@]} || ${#input_jsons[@]} -ne ${#pairwise_csvs[@]} || ${#input_jsons[@]} -ne ${#bugwise_csvs[@]} ]]; then
	echo "Error: Array length mismatch." >&2
	exit 1
fi

for i in "${!input_jsons[@]}"; do
	input_json="${input_jsons[$i]}"
	patches_dir="${patches_dirs[$i]}"
	ast_json="${ast_jsons[$i]}"
	out_csv="${output_csvs[$i]}"
	pair_csv="${pairwise_csvs[$i]}"
	bugwise_csv="${bugwise_csvs[$i]}"

	echo "Running hunk divergence for input_json=$input_json"
    
    # Ensure input exists
    if [[ ! -f "$input_json" ]]; then
        echo "Warning: input JSON not found: $input_json" >&2
        continue
    fi

    # Ensure patches directory exists
    if [[ ! -d "$patches_dir" ]]; then
        echo "Warning: patches directory not found: $patches_dir" >&2
        continue
    fi
    
    # Ensure AST JSON exists
    if [[ ! -f "$ast_json" ]]; then
        echo "Warning: AST JSON not found: $ast_json" >&2
        continue
    fi

    # Ensure output directories exist
    mkdir -p "$(dirname "$out_csv")"
    mkdir -p "$(dirname "$pair_csv")"
    mkdir -p "$(dirname "$bugwise_csv")"

	python3 "${script_dir}/0_hunk_divergence.py" \
        --json "$input_json" \
        --work-dir "$work_dir" \
        --patches-dir "$patches_dir" \
        --ast-json "$ast_json" \
        --out "$out_csv" \
        --pair-out "$pair_csv"

    # Compute bugwise total divergence using output files
    if [[ -f "$out_csv" && -f "$pair_csv" ]]; then
        echo "Computing bugwise total divergence for input_json=$input_json"
        python3 "${script_dir}/1_compute_bugwise_total_divergence.py" \
            --pairwise "$pair_csv" \
            --total "$out_csv" \
            --out "$bugwise_csv"
    fi
done
