#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"

python_script="$script_dir/0_d4j_json_creator_new.py"
work_dir="${WORK_DIR:-$repo_root/checkout-bugs-final}"

patch_dirs=(
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

output_dirs=(
	"${repo_root}/hunk4j/dataset/claude/LocalNoTests"
    "${repo_root}/hunk4j/dataset/claude/LocalTests"
    "${repo_root}/hunk4j/dataset/claude/NonLocalNoTests"
    "${repo_root}/hunk4j/dataset/claude/NonLocalTests"

    "${repo_root}/hunk4j/dataset/codex/LocalNoTests"
    "${repo_root}/hunk4j/dataset/codex/LocalTests"
    "${repo_root}/hunk4j/dataset/codex/NonLocalNoTests"
    "${repo_root}/hunk4j/dataset/codex/NonLocalTests"

    "${repo_root}/hunk4j/dataset/gemini/LocalNoTests"
    "${repo_root}/hunk4j/dataset/gemini/LocalTests"
    "${repo_root}/hunk4j/dataset/gemini/NonLocalNoTests"
    "${repo_root}/hunk4j/dataset/gemini/NonLocalTests"
)

if [[ ${#patch_dirs[@]} -ne ${#output_dirs[@]} ]]; then
	echo "Error: patch_dirs and output_dirs must have the same number of entries." >&2
	exit 1
fi

for i in "${!patch_dirs[@]}"; do
	patch_dir="${patch_dirs[$i]}"
	output_dir="${output_dirs[$i]}"

	echo "Running JSON creator for patch_dir=$patch_dir output_dir=$output_dir"
	python3 "$python_script" \
		--patches_dir "$patch_dir" \
		--work_dir "$work_dir" \
		--output_dir "$output_dir"
done
