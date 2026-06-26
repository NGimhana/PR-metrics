#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"

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

output_jsons=(
	"${script_dir}/claude/LocalNoTests/AST.json"
    "${script_dir}/claude/LocalTests/AST.json"
    "${script_dir}/claude/NonLocalNoTests/AST.json"
    "${script_dir}/claude/NonLocalTests/AST.json"

    "${script_dir}/codex/LocalNoTests/AST.json"
    "${script_dir}/codex/LocalTests/AST.json"
    "${script_dir}/codex/NonLocalNoTests/AST.json"
    "${script_dir}/codex/NonLocalTests/AST.json"

    "${script_dir}/gemini/LocalNoTests/AST.json"
    "${script_dir}/gemini/LocalTests/AST.json"
    "${script_dir}/gemini/NonLocalNoTests/AST.json"
    "${script_dir}/gemini/NonLocalTests/AST.json"
)

if [[ ${#input_jsons[@]} -ne ${#output_jsons[@]} ]]; then
	echo "Error: input_jsons and output_jsons must have the same number of entries." >&2
	exit 1
fi

for i in "${!input_jsons[@]}"; do
	input_json="${input_jsons[$i]}"
	output_json="${output_jsons[$i]}"

	echo "Running AST parser for input_json=$input_json output_json=$output_json"
    # Ensure input exists
    if [[ ! -f "$input_json" ]]; then
        echo "Warning: input JSON not found: $input_json" >&2
        continue
    fi
    # Ensure output directory exists
    out_dir="$(dirname "$output_json")"
    mkdir -p "$out_dir"
	mvn clean compile exec:java -Dexec.args="$input_json $work_dir $output_json"
done