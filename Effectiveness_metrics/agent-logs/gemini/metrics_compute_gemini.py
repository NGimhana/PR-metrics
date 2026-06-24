### Four metrics compute to based on the Logs.
### Output CSV Format: bug_id,repair,all_tests,passed_tests_after,failed_tests_after,compile_pass,localization
### 1. Compilation
### If the .log file has BUILD SUCCESSFUL string compile_pass = 1 else 0
### 2. Repair
### If the .log file has "BUILD SUCCESSFUL" string and "0 failed" string repair = 1 else 0
### 3. Localization 
### Hgt (𝑏) ⊆ 𝐻 (𝑆𝐴 (𝑏)) Hgt is the ground truth java files is a subset of modified java files in the patch
### If all the ground truth java files are present in the modified java files then localization = 1 else 0

import os
import re
import csv

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

def process_test_result_logs(test_logs_dir):
    test_results = {}
    
    # Verify input directory exists
    if not os.path.exists(test_logs_dir):
        print(f"Error: Test logs directory does not exist: {test_logs_dir}")
        return test_results

    # Iterate through all files in the test logs directory
    for filename in os.listdir(test_logs_dir):
        if not filename.endswith(".log"):
            continue

        input_filepath = os.path.join(test_logs_dir, filename)
        
        try:
            with open(input_filepath, 'r', encoding='utf-8') as f:
                log_text = f.read()

            bug_id = filename.split(".log")[0]
            passed_tests_after = 0
            failed_tests_after = 0
            
            ### === Results: 5 passed, 0 failed ===
            ### Search for the  === Results: line and extract the numbers
            results_match = re.search(r'=== Results: (\d+) passed, (\d+) failed ===', log_text)
            if results_match:
                passed_tests_after = int(results_match.group(1))
                failed_tests_after = int(results_match.group(2))

            num_of_all_tests = passed_tests_after + failed_tests_after
            num_of_passed_tests = passed_tests_after
            num_of_failed_tests = failed_tests_after

            test_results[bug_id] = {
                "repair": 1 if (num_of_failed_tests == 0 and num_of_passed_tests == num_of_all_tests) else 0,
                "all_tests": num_of_all_tests,
                "passed_tests_after": num_of_passed_tests,
                "failed_tests_after": num_of_failed_tests
            }

        except Exception as e:
            print(f"Error processing '{filename}': {e}")

    return test_results


def process_telemetry_logs(telemetry_logs_dir, test_results, gt_results, output_file_path):
    start_marker = "gen_ai.output.messages"
    end_marker = "gen_ai.operation.name"
    
    # Regex to find .java files
    java_regex = r'[\w/\\.-]+\.java'

    # Store all parsed records here
    all_results = []

    # Verify input directory exists
    if not os.path.exists(telemetry_logs_dir):
        print(f"Error: Input directory does not exist: {telemetry_logs_dir}")
        return

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Iterate through all files in the input directory
    for filename in os.listdir(telemetry_logs_dir):
        ## Process ONLY files ending with _telemetry.log
        if not filename.endswith("_telemetry.log"):
            continue

        input_filepath = os.path.join(telemetry_logs_dir, filename)
        
        try:
            with open(input_filepath, 'r', encoding='utf-8') as f:
                log_text = f.read()

            ### Note: This is a workaround because the Agent does not always produce any patches.
            ### So we need to check if the log contains the start and ending markers.
            ### Step 1: Find the LAST occurrence of the start_marker
            start_idx = log_text.rfind(start_marker)
            if start_idx == -1:
                print(f"Skipping '{filename}': Could not find '{start_marker}'.")
                continue

            text_search_start = start_idx + len(start_marker)

            # Step 2: Find the NEXT occurrence of the end_marker
            end_idx = log_text.find(end_marker, text_search_start)

            # Step 3: Extract the text
            if end_idx == -1:
                extracted_text = log_text[text_search_start:]
            else:
                extracted_text = log_text[text_search_start:end_idx]

            extracted_text = extracted_text.strip()

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
            bug_id = filename.split("_")[0]
            
            repair_success = test_results.get(bug_id, {}).get("repair", 0)
            all_tests = test_results.get(bug_id, {}).get("all_tests", 0)
            passed_tests_after = test_results.get(bug_id, {}).get("passed_tests_after", 0)
            failed_tests_after = test_results.get(bug_id, {}).get("failed_tests_after", 0)

            # Step 6: Compute localization metric
            localization = 0
            gt_files = gt_results.get(bug_id, {}).get("modified_java_files", [])
            num_of_gt_files = gt_results.get(bug_id, {}).get("num_of_modified_java_files", 0)
            localization = 0
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
        
        with open(output_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_results:
                writer.writerow(row)
                
        print(f"\nExtraction complete. Saved {len(all_results)} records to '{output_file_path}'")
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

    telemetry_logs = ["results_localized_notetsts", "results_localized_withtests", "results-nonlocal-notests", "results_nonlocal_withtests"]
    
    test_result_logs = ["all-test-run-local-notests", "all-test-run-local-tests", "all-test-run-nonlocal-notests", "all-test-run-nonlocal-tests"]

    for setting, telemetry_log, test_result_log in zip(settings, telemetry_logs, test_result_logs):
        setting_path = f"Effectiveness_metrics/agent-logs/gemini/{setting}"
        telemetry_path = os.path.join(setting_path, telemetry_log)
        test_result_path = os.path.join(setting_path, test_result_log)
        
        ## process test result logs to get the test results for each bug_id
        test_results = process_test_result_logs(test_result_path)

        ## process ground truth patch files to get the modified java files for each bug_id
        gt_patch_dir = os.path.join("patches/merged_patches_final")
        gt_patch_files = process_gt_patch_java_files(gt_patch_dir)

        # Updated output path to save as a single CSV file
        output_csv_path = os.path.join(setting_path, f"{setting}_localisation_metrics.csv")
        
        print("Starting extraction process...\n")
        process_telemetry_logs(telemetry_path, test_results, gt_patch_files, output_csv_path)