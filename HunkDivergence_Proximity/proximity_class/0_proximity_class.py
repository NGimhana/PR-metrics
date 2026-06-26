#!/usr/bin/env python3
import json, argparse, re, csv, statistics, math, os
from itertools import combinations
from pathlib import PurePosixPath, Path
from typing import List, Dict, Optional, Tuple
import javalang
import javalang.tree

def longest_common_prefix(a: List[str], b: List[str]) -> int:
    depth = 0
    for x, y in zip(a, b):
        if x == y:
            depth += 1
        else:
            break
    return depth

class Hunk:
    __slots__ = ("file", "method", "pkg")
    def __init__(self, file_path: str, method: str, pkg: List[str]):
        self.file = file_path
        self.method = method
        self.pkg = pkg

_parent_map: Dict[javalang.tree.Node, javalang.tree.Node] = {}

def annotate_parents(node: javalang.tree.Node,
                     parent: Optional[javalang.tree.Node] = None) -> None:
    if not isinstance(node, javalang.tree.Node):
        return
    if parent is not None:
        _parent_map[node] = parent
    for child in node.children:
        if isinstance(child, list):
            for c in child:
                annotate_parents(c, node)
        else:
            annotate_parents(child, node)

def _lca(u: Optional[javalang.tree.Node],
         v: Optional[javalang.tree.Node]) -> Optional[javalang.tree.Node]:
    seen = set()
    x = u
    while x is not None:
        seen.add(x)
        x = _parent_map.get(x)
    y = v
    while y is not None and y not in seen:
        y = _parent_map.get(y)
    return y

def build_ast_tree(src: str) -> Optional[javalang.tree.Node]:
    try:
        return javalang.parse.parse(src)
    except Exception:
        return None

def find_enclosing_method(node: Optional[javalang.tree.Node]) -> str:
    curr = node
    while curr is not None:
        if isinstance(curr, javalang.tree.MethodDeclaration):
            params = []
            for p in curr.parameters:
                tname = getattr(p.type, "name", None) or str(p.type)
                params.append(tname)
            return f"{curr.name}({','.join(params)})"
        elif isinstance(curr, javalang.tree.ConstructorDeclaration):
            params = []
            for p in curr.parameters:
                tname = getattr(p.type, "name", None) or str(p.type)
                params.append(tname)
            return f"{curr.name}({','.join(params)})"
        curr = _parent_map.get(curr)
    return "<unknown>"

def parse_patch_file(patch_path: Path):
    out, idx, buggy, fixed, in_hunk = {}, 0, [], [], False
    curr_start, curr_end = None, None
    curr_file = None
    with patch_path.open(encoding="utf-8") as pf:
        for line in pf:
            if line.startswith("+++ ") or line.startswith("--- "):
                match_file = re.match(r"^(?:\+\+\+|\-\-\-)\s+(?:[ab]/)?(.*)$", line)
                if match_file:
                    file_cand = match_file.group(1).strip()
                    if file_cand != "/dev/null":
                        curr_file = file_cand
                continue
            if line.startswith("@@"):
                if in_hunk:
                    out[idx] = {
                        "buggy": buggy,
                        "fixed": fixed,
                        "start_line": curr_start,
                        "end_line": curr_end,
                        "file": curr_file
                    }
                    idx += 1
                buggy, fixed, in_hunk = [], [], True
                match = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
                if match:
                    curr_start = int(match.group(1))
                    original_len = int(match.group(2)) if match.group(2) else 1
                    curr_end = curr_start + original_len - 1
                else:
                    curr_start, curr_end = None, None
                continue
            if not in_hunk:
                continue
            if line.startswith("+") and not line.startswith("+++"):
                fixed.append(line[1:].rstrip("\n"))
            elif line.startswith("-") and not line.startswith("---"):
                buggy.append(line[1:].rstrip("\n"))
    if in_hunk:
        out[idx] = {
            "buggy": buggy,
            "fixed": fixed,
            "start_line": curr_start,
            "end_line": curr_end,
            "file": curr_file
        }
    return out

def build_hunks(bug_id: str, work_dir: str, defects4j_home: str) -> List[Hunk]:
    hunks = []
    
    # proj, num = bug_id.split("_")
    bug_id = bug_id
    # checkout_root = Path(work_dir) / f"{proj}_{num}"
    checkout_root = Path(work_dir)
    # patch_root = Path(defects4j_home) / "framework" / "projects" / proj / "patches"
    patch_root = Path(defects4j_home)
    

    # patch_file = patch_root / f"{num}.src.patch"
    patch_file = patch_root / f"{bug_id}.patch"
    patch_hunks = parse_patch_file(patch_file) if patch_file.exists() else {}

    for hunk_id, ph in patch_hunks.items():
        ## only consider .java files
        if not ph.get("file", "").endswith(".java"):
            continue
        file_rel = ph.get("file", "MISSING_FILE")
        start = ph.get("start_line", 0)
        end = ph.get("end_line", 0)

        fp = checkout_root / file_rel
        if not fp.exists():
            alt = checkout_root.joinpath(*file_rel.split("/")[1:])
            fp = alt if alt.exists() else None
            
        if not fp or not fp.exists():
            pkg = list(PurePosixPath(file_rel).parts[1:-1]) if "/" in file_rel else []
            hunks.append(Hunk(file_rel, f"unknown_method_{hunk_id}", pkg))
            continue

        src_lines = fp.read_text(errors="ignore").splitlines()
        pkg       = list(PurePosixPath(file_rel).parts[1:-1]) if "/" in file_rel else []
        
        _parent_map.clear()
        
        tree = build_ast_tree("\n".join(src_lines))
        if tree:
            annotate_parents(tree)

        subtree_root = tree
        method_name = f"unknown_method_{hunk_id}"
        if tree:
            buggy_nodes = []
            for _, node in tree:
                pos = getattr(node, "position", None)
                if pos and (start <= pos[0] <= end or end <= pos[0] <= start):
                    buggy_nodes.append(node)

            if buggy_nodes:
                root = buggy_nodes[0]
                for node in buggy_nodes[1:]:
                    root = _lca(root, node)
                subtree_root = root
                method_name = find_enclosing_method(subtree_root)

        hunks.append(Hunk(file_rel, method_name, pkg))

    return hunks


def SF(H):
    return len({h.file for h in H}) == 1

def SM(H):
    return len({h.method for h in H}) == 1

def SP(H):
    return len({tuple(h.pkg) for h in H}) == 1

def LCP_min(H):
    return 0 if len(H) < 2 else min(longest_common_prefix(a.pkg, b.pkg) for a, b in combinations(H, 2))


def classify(H, cutoff):
    if SF(H):
        return "Nucleus" if SM(H) else "Cluster"
    if SP(H):
        return "Orbit"
    return "Sprawl" if LCP_min(H) > cutoff else "Fragment"


def main():
    ap = argparse.ArgumentParser(description="Spatial proximity classification")
    ap.add_argument("input_json", nargs="?", default="hunk4j/dataset/d4j_dataset_final.json")
    ap.add_argument("output_csv", nargs="?", default="HunkDivergence_Proximity/proximity_class/proximity_class_new.csv")
    ap.add_argument("--work-dir", default="checkout-bugs-final")
    # ap.add_argument('--defects4j_home', type=str, default="/Users/nadeeshan/Desktop/PR/birch/defects4j-2.0.1",
    #                 help='Path to the Defects4J home directory')
    ap.add_argument('--defects4j_home', type=str, default="patches/new_patches",
                    help='Path to the Defects4J home directory')
    
    ap.add_argument("--threshold", type=int, help="Override LCP cutoff for Sprawl")
    args = ap.parse_args()

    data = json.load(open(args.input_json, encoding="utf-8"))

    pkg_depths = []
    for bug_id in data.keys():
        H = build_hunks(bug_id, args.work_dir, args.defects4j_home)
        pkg_depths.extend(len(h.pkg) for h in H)

    median_depth = statistics.median(pkg_depths) if pkg_depths else 0
    default_cutoff = math.floor(median_depth / 2)
    cutoff = args.threshold if args.threshold is not None else default_cutoff

    print(f"Median package depth = {median_depth}; cutoff = {cutoff}")

    rows = [("bug_id", "proximity_class")]
    for bug_id in data.keys():
        H = build_hunks(bug_id, args.work_dir, args.defects4j_home)
        rows.append((bug_id, classify(H, cutoff)))

    with open(args.output_csv, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)
    print(f"Wrote {len(rows)-1} rows → {args.output_csv}")

if __name__ == "__main__":
    main()
