import csv
import os
import re

## bug_id,repair,all_tests,passed_tests_after,failed_tests_after,compile_pass,modified_java_files,num_of_modified_java_files,gt_files,num_of_gt_files,localization

def process_gt_patch_java_files(gt_patch_dir):
    gt_patch_files = {}
    
    # Verify input directory exists
    if not os.path.exists(gt_patch_dir):
        print(f"Error: Ground truth patch directory does not exist: {gt_patch_dir}")
        return gt_patch_files

    # Iterate through all files in the ground truth patch directory
    for filename in os.listdir(gt_patch_dir):
        if not filename.endswith(".patch"):
            continue

        input_filepath = os.path.join(gt_patch_dir, filename)
        
        try:
            with open(input_filepath, 'r', encoding='utf-8') as f:
                patch_text = f.read()

            bug_id = filename.split(".patch")[0]
            java_files = re.findall(r'[\w/\\.-]+\.java', patch_text)
            java_files = [os.path.basename(f) for f in java_files]  # Extract only the file names
            num_of_java_files = len(set(java_files))  # Use set to avoid duplicates

            gt_patch_files[bug_id] = {
                "modified_java_files": str(list(set(java_files))),  # Save as string representation of list
                "num_of_modified_java_files": num_of_java_files
            }

        except Exception as e:
            print(f"Error processing '{filename}': {e}")

    return gt_patch_files

def process_telemtery_logs(setting, gt_results, telemetry_log, output_csv_path):
    
    setting_path = f"Effectiveness_metrics/agent-logs/codex/{setting}"
    telemetry_logs_dir = os.path.join(setting_path, telemetry_log)

    # Regex to find .java files
    java_regex = r'[\w/\\.-]+\.java'

    # Store all parsed records here
    all_results = []

    # Verify input directory exists
    if not os.path.exists(telemetry_logs_dir):
        print(f"Error: Input directory does not exist: {telemetry_logs_dir}")
        return

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_csv_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Iterate through all files in the input directory
    for log_file_dir in os.listdir(telemetry_logs_dir):
        ## check whether the log_file_dir is a directory
        if not os.path.isdir(os.path.join(telemetry_logs_dir, log_file_dir)):
            continue
        log_file_dir_path = os.path.join(telemetry_logs_dir, log_file_dir, "logs")

        if not os.path.isdir(log_file_dir_path):
            continue

        jsonl_files = [name for name in os.listdir(log_file_dir_path) if name.endswith(".jsonl")]
        if jsonl_files:
            candidate_files = sorted(jsonl_files)
        elif (log_file_dir == "log-92" or log_file_dir == "log-192" or log_file_dir == "log-1151" or log_file_dir == "log-1207") and setting == "Localized_With_No_Tests":
            candidate_files = sorted([name for name in os.listdir(log_file_dir_path) if name.endswith(".log")])
        elif (log_file_dir == "log-54" or log_file_dir == "log-191" or log_file_dir == "log-1445") and setting == "Localized_With_Tests":
            candidate_files = sorted([name for name in os.listdir(log_file_dir_path) if name.endswith(".log")])
        elif (log_file_dir == "log-92") and setting == "Non_Localized_With_No_Tests":
            candidate_files = sorted([name for name in os.listdir(log_file_dir_path) if name.endswith(".log")])
        else:
            candidate_files = []

        for filename in candidate_files:


            input_filepath = os.path.join(telemetry_logs_dir, log_file_dir, "logs", filename)
            
            try:
                with open(input_filepath, 'r', encoding='utf-8') as f:
                    log_text = f.read()

                ### Note: This is a workaround because the Agent does not always produce any patches.
                ### So we need to check if the log contains string *** Begin Patch\n*** Update File:
                ### Step 1: Extract all the lines that contains *** Begin Patch\n*** Update File:
                if filename.endswith(".log"):
                    modified_files = re.findall(r'^\+\+\+ b/([\w/\\.\-]+\.java)', log_text, re.MULTILINE)
                    extracted_text = "\n".join(modified_files)
                else:
                    edit_lines = re.findall(r'\*\*\* Update File:\s*(.*)', log_text)
                    ## merge all the edit_lines into a single string to search for .java files
                    extracted_text = "\n".join(edit_lines)


                # Step 4: Extract the .java files using Regex
                # Wrapping in list(set(...)) removes any duplicate files found in the same log
                ## if "/" present in the file path then split by "/" and take the last part of the path to get the file name only
                modified_java_files = list(set(re.findall(java_regex, extracted_text)))
                modified_java_files = [os.path.basename(f) for f in modified_java_files]
                num_of_modified_java_files = len(modified_java_files)

                # Step 5: Parse the JSON and extract the requested fields
                bug_id, repair, all_tests = "", "", ""
                passed_tests_after, failed_tests_after, compile_pass = "", "", ""

                ## if log_text contains "BUILD SUCCESSFUL" then compile_pass = 1 else 0
                compile_pass = 1 if "BUILD SUCCESSFUL" in log_text else 0 
                bug_id = "bug-" + log_file_dir.split("-")[1]
                
                ## Missing Test excution results
                if setting in ["Localized_With_No_Tests", "Non_Localized_With_No_Tests"]:
                    # repair_success = test_results.get(bug_id, {}).get("repair", 0)
                    # all_tests = test_results.get(bug_id, {}).get("all_tests", 0)
                    # passed_tests_after = test_results.get(bug_id, {}).get("passed_tests_after", 0)
                    # failed_tests_after = test_results.get(bug_id, {}).get("failed_tests_after", 0)
                    repair_success = 0
                    all_tests = 0
                    passed_tests_after = 0
                    failed_tests_after = 0
                else:
                    passed_tests_after = 0
                    failed_tests_after = 0
                    
                    ### Search for last ocurance of string "./run_pipeline.sh all" and extract the rest of the text after that string
                    ### Search for <number> passed, <number> failed or pass=<number> fail=<number> in the rest of the text and extract the numbers
                    marker = "./run_pipeline.sh all"
                    marker_index = log_text.rfind(marker)
                    rest_text = log_text[marker_index + len(marker):] if marker_index != -1 else log_text

                    results_matches = re.findall(
                        r'(\d+)\s+passed,\s*(\d+)\s+failed|pass=(\d+)\s+fail=(\d+)',
                        rest_text,
                    )
                    if results_matches:
                        last_results_match = results_matches[-1]  # Get the last match
                        if last_results_match[0] and last_results_match[1]:
                            passed_tests_after = int(last_results_match[0])
                            failed_tests_after = int(last_results_match[1])
                        else:
                            passed_tests_after = int(last_results_match[2])
                            failed_tests_after = int(last_results_match[3])

                    all_tests = passed_tests_after + failed_tests_after
                    repair_success = 1 if (failed_tests_after == 0 and passed_tests_after == all_tests) else 0
                    

                # Step 6: Compute localization metric
                localization = 0
                gt_files = gt_results.get(bug_id, {}).get("modified_java_files", [])
                num_of_gt_files = gt_results.get(bug_id, {}).get("num_of_modified_java_files", 0)
                
                ## search thorough the modified_java_files and check if all the gt_files are present in the modified_java_files
                count = 0
                import ast
                for gt_file in ast.literal_eval(gt_files):
                    if gt_file in modified_java_files:
                        count += 1
                if count == num_of_gt_files and num_of_gt_files > 0:
                    localization = 1    

                # Append the structured dictionary to our results list
                all_results.append({
                    "bug_id": bug_id,  # Extract bug_id from filename
                    "repair": repair_success,  # Use the getRpairStatus function to determine repair status
                    "all_tests": all_tests,
                    "passed_tests_after": passed_tests_after,
                    "failed_tests_after": failed_tests_after,
                    "compile_pass": compile_pass,
                    "modified_java_files": str(modified_java_files), # Saves as "['file1.java', 'file2.java']"
                    "num_of_modified_java_files": num_of_modified_java_files,
                    "gt_files": str(gt_files),  # Saves as "['file1.java', 'file2.java']"
                    "num_of_gt_files": num_of_gt_files,
                    "localization": localization
                })

                print(f"Processed: '{filename}'")

            except Exception as e:
                print(f"Error processing '{filename}': {e}")

    # Step 7: Save everything to a CSV file
    if all_results:
        fieldnames = [
            "bug_id", "repair", "all_tests", "passed_tests_after", 
            "failed_tests_after", "compile_pass", "modified_java_files", 
            "num_of_modified_java_files",
            "gt_files","num_of_gt_files","localization"
        ]
        
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_results:
                writer.writerow(row)
                
        print(f"\nExtraction complete. Saved {len(all_results)} records to '{output_csv_path}'")
    else:
        print("\nNo valid logs were processed. Output file was not created.")






# ==========================================
# Execution
# ==========================================
if __name__ == "__main__":

    settings = ["Localized_With_No_Tests",
                "Localized_With_Tests",
                "Non_Localized_With_No_Tests",
                "Non_Localized_With_Tests"]

    telemetry_logs = ["resultsLocNoTests", "results-localization", "resultsNonLocNoTests", "results-woLocalization"]
    

    for setting, telemetry_log in zip(settings, telemetry_logs):
        print(f"\n{'='*60}")
        print(f"Processing: {setting} / {telemetry_log}")
        print(f"{'='*60}")
        
        ## process ground truth patch files to get the modified java files for each bug_id
        gt_patch_dir = os.path.join("patches/merged_patches_final")
        gt_patch_files = process_gt_patch_java_files(gt_patch_dir)

        setting_path = f"Effectiveness_metrics/agent-logs/codex/{setting}"
        # Updated output path to save as a single CSV file
        output_csv_path = os.path.join(setting_path, f"{setting}_localisation_metrics.csv")

        process_telemtery_logs(setting, gt_patch_files, telemetry_log, output_csv_path)