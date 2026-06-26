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

divergence_csvs=(
	"${repo_root}/HunkDivergence_Proximity/hunk_divergence/claude/LocalNoTests/total_hunk_divergence.csv"
    "${repo_root}/HunkDivergence_Proximity/hunk_divergence/claude/LocalTests/total_hunk_divergence.csv"
    "${repo_root}/HunkDivergence_Proximity/hunk_divergence/claude/NonLocalNoTests/total_hunk_divergence.csv"
    "${repo_root}/HunkDivergence_Proximity/hunk_divergence/claude/NonLocalTests/total_hunk_divergence.csv"

    "${repo_root}/HunkDivergence_Proximity/hunk_divergence/codex/LocalNoTests/total_hunk_divergence.csv"
    "${repo_root}/HunkDivergence_Proximity/hunk_divergence/codex/LocalTests/total_hunk_divergence.csv"
    "${repo_root}/HunkDivergence_Proximity/hunk_divergence/codex/NonLocalNoTests/total_hunk_divergence.csv"
    "${repo_root}/HunkDivergence_Proximity/hunk_divergence/codex/NonLocalTests/total_hunk_divergence.csv"
    
    "${repo_root}/HunkDivergence_Proximity/hunk_divergence/gemini/LocalNoTests/total_hunk_divergence.csv"
    "${repo_root}/HunkDivergence_Proximity/hunk_divergence/gemini/LocalTests/total_hunk_divergence.csv"
    "${repo_root}/HunkDivergence_Proximity/hunk_divergence/gemini/NonLocalNoTests/total_hunk_divergence.csv"
    "${repo_root}/HunkDivergence_Proximity/hunk_divergence/gemini/NonLocalTests/total_hunk_divergence.csv"
)

proximity_csvs=(
	"${script_dir}/claude/LocalNoTests/proximity_class.csv"
    "${script_dir}/claude/LocalTests/proximity_class.csv"
    "${script_dir}/claude/NonLocalNoTests/proximity_class.csv"
    "${script_dir}/claude/NonLocalTests/proximity_class.csv"

    "${script_dir}/codex/LocalNoTests/proximity_class.csv"
    "${script_dir}/codex/LocalTests/proximity_class.csv"
    "${script_dir}/codex/NonLocalNoTests/proximity_class.csv"
    "${script_dir}/codex/NonLocalTests/proximity_class.csv"
    
    "${script_dir}/gemini/LocalNoTests/proximity_class.csv"
    "${script_dir}/gemini/LocalTests/proximity_class.csv"
    "${script_dir}/gemini/NonLocalNoTests/proximity_class.csv"
    "${script_dir}/gemini/NonLocalTests/proximity_class.csv"
)

proximity_avg_csvs=(
	"${script_dir}/claude/LocalNoTests/proximity_class_avg_hunk_divergence.csv"
    "${script_dir}/claude/LocalTests/proximity_class_avg_hunk_divergence.csv"
    "${script_dir}/claude/NonLocalNoTests/proximity_class_avg_hunk_divergence.csv"
    "${script_dir}/claude/NonLocalTests/proximity_class_avg_hunk_divergence.csv"

    "${script_dir}/codex/LocalNoTests/proximity_class_avg_hunk_divergence.csv"
    "${script_dir}/codex/LocalTests/proximity_class_avg_hunk_divergence.csv"
    "${script_dir}/codex/NonLocalNoTests/proximity_class_avg_hunk_divergence.csv"
    "${script_dir}/codex/NonLocalTests/proximity_class_avg_hunk_divergence.csv"
    
    "${script_dir}/gemini/LocalNoTests/proximity_class_avg_hunk_divergence.csv"
    "${script_dir}/gemini/LocalTests/proximity_class_avg_hunk_divergence.csv"
    "${script_dir}/gemini/NonLocalNoTests/proximity_class_avg_hunk_divergence.csv"
    "${script_dir}/gemini/NonLocalTests/proximity_class_avg_hunk_divergence.csv"
)

# Validate arrays have same lengths
if [[ ${#input_jsons[@]} -ne ${#patches_dirs[@]} || ${#input_jsons[@]} -ne ${#divergence_csvs[@]} || ${#input_jsons[@]} -ne ${#proximity_csvs[@]} || ${#input_jsons[@]} -ne ${#proximity_avg_csvs[@]} ]]; then
	echo "Error: Array length mismatch." >&2
	exit 1
fi

for i in "${!input_jsons[@]}"; do
	input_json="${input_jsons[$i]}"
	patches_dir="${patches_dirs[$i]}"
	div_csv="${divergence_csvs[$i]}"
	prox_csv="${proximity_csvs[$i]}"
	prox_avg_csv="${proximity_avg_csvs[$i]}"

	echo "Running spatial proximity classification for input_json=$input_json"
    
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

    # Ensure output directories exist
    mkdir -p "$(dirname "$prox_csv")"
    mkdir -p "$(dirname "$prox_avg_csv")"

	python3 "${script_dir}/0_proximity_class.py" \
        "$input_json" \
        "$prox_csv" \
        --work-dir "$work_dir" \
        --defects4j_home "$patches_dir"

    # Compute average hunk divergence for each proximity class
    if [[ -f "$prox_csv" ]]; then
        # Check if the divergence input file exists
        if [[ ! -f "$div_csv" ]]; then
            echo "Warning: divergence CSV not found: $div_csv. Skipping average computation." >&2
            continue
        fi

        echo "Computing average hunk divergence per proximity class for input_json=$input_json"
        python3 "${script_dir}/1_proximity_class_avg_hunk_divergence.py" \
            --divergence_csv "$div_csv" \
            --proximity_csv "$prox_csv" \
            --output_csv "$prox_avg_csv"
    fi
done
