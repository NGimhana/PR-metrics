from pathlib import Path
import re


INPUT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(__file__).resolve().parent / "merged_patches_final"


def extract_bug_id(filename: str) -> str | None:
    match = re.search(r"(\d+)", filename)
    return match.group(1) if match else None


def merge_patches() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    grouped_files: dict[str, list[Path]] = {}
    for patch_file in sorted(INPUT_DIR.iterdir()):
        if not patch_file.is_file():
            continue

        bug_id = extract_bug_id(patch_file.name)
        if bug_id is None:
            continue

        grouped_files.setdefault(bug_id, []).append(patch_file)

    for bug_id, patch_files in grouped_files.items():
        merged_parts: list[str] = []

        for patch_file in patch_files:
            content = patch_file.read_text(encoding="utf-8", errors="replace").rstrip()
            if content:
                merged_parts.append(content)

        output_file = OUTPUT_DIR / f"bug-{bug_id}.patch"
        output_file.write_text("\n\n".join(merged_parts) + ("\n" if merged_parts else ""), encoding="utf-8")
        print(f"Wrote {output_file} from {len(patch_files)} patch file(s)")


if __name__ == "__main__":
    merge_patches()