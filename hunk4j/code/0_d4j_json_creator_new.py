import os
import re
import argparse
import json

def get_buggy_lines(patch_file_path):
    buggy_lines = {}
    if not os.path.exists(patch_file_path):
        return buggy_lines
    try:
        with open(patch_file_path, 'r', encoding='utf-8') as patch_file:
            lines = patch_file.readlines()
    except UnicodeDecodeError:
        try:
            with open(patch_file_path, 'r', encoding='ISO-8859-1') as patch_file:
                lines = patch_file.readlines()
        except IOError:
            return buggy_lines
    except IOError:
        return buggy_lines

    current_file = None
    for line in lines:
        if line.startswith('---'):
            parts = line.split(' ')
            if len(parts) >= 2:
                current_file = None
                candidate = parts[1].strip()
                if candidate.startswith('a/'):
                    candidate = candidate[2:]
                java_index = candidate.find('.java')
                if java_index != -1:
                    current_file = candidate[:java_index + 5]
        if line.startswith('@@'):
            match = re.search(r'\+(\d+),(\d+)', line)
            if match and current_file:
                start_line = int(match.group(1))
                line_count = int(match.group(2))
                end_line = start_line + line_count
                if current_file not in buggy_lines:
                    buggy_lines[current_file] = []
                buggy_lines[current_file].append((start_line, end_line))
    return buggy_lines

def process_patches(patches_dir, work_dir, output_dir):
    hunks_data = {}
    
    if not os.path.exists(patches_dir):
        print(f"Error: Patches directory {patches_dir} does not exist")
        return
        
    for filename in sorted(os.listdir(patches_dir)):
        if filename.endswith(".patch"):
            key = filename[:-6] # Strip ".patch"
            print(f"Processing patch {filename} (key: {key})...")
            
            patch_file_path = os.path.join(patches_dir, filename)
            buggy_lines = get_buggy_lines(patch_file_path)
            
            hunks = []
            for buggy_file, buggy_lines_list in buggy_lines.items():
                # Read original file to count lines if it exists
                original_file_path = os.path.join(work_dir, key, buggy_file)
                line_count_file = 10000  # Default fallback
                if os.path.exists(original_file_path):
                    try:
                        with open(original_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            line_count_file = len(f.readlines())
                    except IOError:
                        pass
                
                for start_line, end_line in sorted(buggy_lines_list, key=lambda x: x[1]):
                    # Determine end_index
                    if end_line - 3 > start_line + 2 or 0 <= start_line <= 3:
                        end_index = end_line - 4
                    else:
                        end_index = start_line + 3
                        
                    # Determine start_index
                    if start_line + 2 < end_line - 3 or line_count_file - 2 <= end_line <= line_count_file + 1:
                        start_index = start_line + 3
                    else:
                        start_index = end_line - 2
                        
                    hunks.append({
                        'file': buggy_file,
                        'start_line': start_index,
                        'end_line': end_index
                    })
            
            if hunks:
                hunks_data[key] = {
                    "buggy_hunks": {str(i): hunk for i, hunk in enumerate(hunks)}
                }

    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, 'd4j_dataset_final.json')
    with open(output_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(hunks_data, json_file, ensure_ascii=False, indent=4)
    print(f"Saved minimal dataset JSON to {output_file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process patch files and create minimal JSON with buggy hunk locations.')
    parser.add_argument('--patches_dir', type=str, default="patches/new_patches", help='Directory containing the patch files')
    parser.add_argument('--work_dir', type=str, default="checkout-bugs-final", help='Working directory where repositories are checked out')
    parser.add_argument('--output_dir', type=str, default="hunk4j/dataset", help='Output directory for the generated JSON')

    args = parser.parse_args()

    process_patches(args.patches_dir, args.work_dir, args.output_dir)
