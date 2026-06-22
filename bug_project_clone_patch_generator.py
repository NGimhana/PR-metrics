### File 2- /Users/nadeeshan/Desktop/PR/birch/PR-metrics/GT_csv/real-bugs-ICSE24-additional - real-bugs.csv
### Extract Bug ID, App Name, Buggy Commit IDs, Fixed Commit IDs

### File 1 - /Users/nadeeshan/Desktop/PR/birch/PR-metrics/GT_csv/real-bugs-ICSE24-additional - code.csv
### Extract columns slug,class_path


import os
import subprocess
import pandas as pd

def clean_slug(s):
    if pd.isna(s):
        return ""
    return "".join(str(s).split()).lower()

# class_path_df = pd.read_csv("PR-metrics/GT_csv/real-bugs-ICSE24-additional - code.csv")
# commit_id_df = pd.read_csv("PR-metrics/GT_csv/real-bugs-ICSE24-additional - real-bugs.csv")
# class_path_df = pd.read_csv("/Users/nadeeshan/Desktop/PR/birch/PR-metrics/GT_csv/AndroR2_dataset - code.csv")
# commit_id_df = pd.read_csv("/Users/nadeeshan/Desktop/PR/birch/PR-metrics/GT_csv/AndroR2_dataset - Bug ID - commits.csv")
#class_path_df = pd.read_csv("/Users/nadeeshan/Desktop/PR/birch/PR-metrics/GT_csv/RealBugs-5Apps - code.csv")
#commit_id_df = pd.read_csv("/Users/nadeeshan/Desktop/PR/birch/PR-metrics/GT_csv/RealBugs-5Apps - real bugs - commits.csv")
class_path_df = pd.read_csv("/Users/nadeeshan/Desktop/PR/birch/PR-metrics/GT_csv/More Real Bugs - code.csv")
commit_id_df = pd.read_csv("/Users/nadeeshan/Desktop/PR/birch/PR-metrics/GT_csv/More Real Bugs - bugs - commits.csv")


# Create directories if they don't exist
projects_dir = os.path.abspath("/Users/nadeeshan/Desktop/PR/birch/PR-metrics/projects")
checkout_dir_base = os.path.abspath("/Users/nadeeshan/Desktop/PR/birch/PR-metrics/checkout-bugs")
patches_dir = os.path.abspath("/Users/nadeeshan/Desktop/PR/birch/PR-metrics/patches")

os.makedirs(projects_dir, exist_ok=True)
os.makedirs(checkout_dir_base, exist_ok=True)
os.makedirs(patches_dir, exist_ok=True)

## iterate through class_path_df
for index, row in class_path_df.iterrows():
    raw_slug = row["slug"]
    class_path = row["class_path"]
    
    ## split the raw_slug into parts based on the number --> output should like ["markor","53","real","makeDialog"]
    tokens = raw_slug.split('-')
        

    # find the first token that is a number
    digit_idx = -1
    for i, token in enumerate(tokens):
        if token.isdigit():
            digit_idx = i
            break
            
    if digit_idx == -1:
        print(f"Warning: Could not find bug ID number in raw_slug: {raw_slug}")
        continue
        
    # connect each token with hyphen upto the number --> "markor-53"
    bug_slug = "-".join(tokens[:digit_idx+1])
    
    # find the particular row in the commit_id_df where slug is "markor-53"
    bug_slug_clean = clean_slug(bug_slug)
    matched = commit_id_df[commit_id_df['slug'].apply(clean_slug) == bug_slug_clean]
    
    if matched.empty:
        print(f"Warning: No match found in commit_id_df for bug slug: {bug_slug} (from {raw_slug})")
        continue
        
    matched_row = matched.iloc[0]
    
    if pd.isna(matched_row['Buggy Commit IDs']) or pd.isna(matched_row['Fixed Commit IDs']):
        print(f"Skipping {raw_slug}: Buggy or Fixed commit ID is NaN")
        continue
        
    bug_id = str(matched_row['Bug ID']).strip()
    app_name = str(matched_row['App Name']).strip()
    buggy_commit = str(matched_row['Buggy Commit IDs']).strip()
    fixed_commit = str(matched_row['Fixed Commit IDs']).strip()
    gh_repo = str(matched_row['GH_repo']).strip()
    
    print(f"\nProcessing: {raw_slug}")
    print(f"  App Name: {app_name}, Bug ID: {bug_id}")
    print(f"  Buggy Commit: {buggy_commit}")
    print(f"  Fixed Commit: {fixed_commit}")
    print(f"  Repo: {gh_repo}")
    
    # Extract repo name from gh_repo URL
    repo_name = gh_repo.rstrip('/').split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
        
    repo_dir = os.path.join(projects_dir, repo_name)
    
    # 1. Clone the repo to projects/ (cache) if not already done
    if not os.path.exists(repo_dir):
        print(f"  Cloning {gh_repo} to cache...")
        subprocess.run(["git", "clone", gh_repo, repo_dir], check=True)
    else:
        print(f"  Repo {repo_name} already exists in cache.")
        
    # 2. Extract the file path inside the repo
    prefix = raw_slug + "/"
    if class_path.startswith(prefix):
        repo_file_path = class_path[len(prefix):]
    else:
        repo_file_path = class_path
        
    # 3. Generate patch in patches/
    patch_file = os.path.join(patches_dir, f"{raw_slug}.patch")
    print(f"  Generating patch for {repo_file_path}...")
    try:
        if raw_slug == "realbug-1640-onCreate-ExerciseViewActivity":
            with open(patch_file, "w") as f_out:
                subprocess.run(
                ["git", "diff", f"{buggy_commit}:app/src/main/java/com/german_software_engineers/trainerapp/ExerciseViewActivity.java", f"{fixed_commit}:app/src/main/java/com/german_software_engineers/trainerapp/ExerciseView/Activity/ExerciseViewActivity.java"],
                cwd=repo_dir,
                stdout=f_out,
                check=True
            )
        elif raw_slug == "realbug-1641-addScheduleToModel" or raw_slug == "realbug-1641-onCreate":
            with open(patch_file, "w") as f_out:
                subprocess.run(
                ["git", "diff", f"{buggy_commit}:app/src/main/java/com/german_software_engineers/trainerapp/GeneralTrainingScheduleEditor.java", f"{fixed_commit}:app/src/main/java/com/german_software_engineers/trainerapp/ScheduleView/GeneralTrainingScheduleEditor.java"],
                cwd=repo_dir,
                stdout=f_out,
                check=True
            )

        elif raw_slug == "realbug-1641-onStart":
            with open(patch_file, "w") as f_out:
                subprocess.run(
                ["git", "diff", f"{buggy_commit}:app/src/main/java/com/german_software_engineers/trainerapp/ExerciseViewActivity.java", f"{fixed_commit}:app/src/main/java/com/german_software_engineers/trainerapp/ExerciseView/Activity/ExerciseViewActivity.java"],
                cwd=repo_dir,
                stdout=f_out,
                check=True
            )
        
        elif raw_slug == "harmonic-real-114-onClick":
            with open(patch_file, "w") as f_out:
                subprocess.run(
                ["git", "diff", f"{buggy_commit}:app/src/main/java/com/simon/harmonichackernews/CommentsRecyclerViewAdapter.java", f"{fixed_commit}:app/src/main/java/com/simon/harmonichackernews/adapters/CommentsRecyclerViewAdapter.java"],
                cwd=repo_dir,
                stdout=f_out,
                check=True
            )
        
        elif raw_slug == "bug-1446-onCreateView" or raw_slug == "bug-1446-updateAllFishingSpots" or raw_slug == "bug-1446-onClick" or raw_slug == "bug-1446-goToManageFishingSpot" :
            with open(patch_file, "w") as f_out:
                subprocess.run(
                ["git", "diff", f"{buggy_commit}:AnglersLog/app/src/main/java/com/cohenadair/anglerslog/locations/ManageLocationFragment.java", f"{fixed_commit}:android/app/src/main/java/com/cohenadair/anglerslog/locations/ManageLocationFragment.java"],
                cwd=repo_dir,
                stdout=f_out,
                check=True
            )

        else: 
            with open(patch_file, "w") as f_out:
                subprocess.run(
                ["git", "diff", buggy_commit, fixed_commit, "--", repo_file_path],
                cwd=repo_dir,
                stdout=f_out,
                check=True
            )
    except Exception as e:
        print(f"Error generating patch for {raw_slug}: {e}")
        continue    
    # 4. Clone to checkout-bugs/<raw_slug> and checkout buggy commit
    dest_checkout_dir = os.path.join(checkout_dir_base, raw_slug)
    if not os.path.exists(dest_checkout_dir):
        print(f"  Creating checkout directory for buggy commit at {dest_checkout_dir}...")
        # Clone locally from cache to avoid downloading again
        subprocess.run(["git", "clone", repo_dir, dest_checkout_dir], check=True)
        # Checkout the buggy commit
        subprocess.run(["git", "checkout", buggy_commit], cwd=dest_checkout_dir, check=True)
    else:
        print(f"  Checkout directory {dest_checkout_dir} already exists.")