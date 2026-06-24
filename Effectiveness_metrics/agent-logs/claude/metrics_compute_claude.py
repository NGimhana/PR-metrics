import csv
import os
import re

## bug_id,repair,all_tests,passed_tests_after,failed_tests_after,compile_pass,modified_java_files,num_of_modified_java_files,gt_files,num_of_gt_files,localization
def process_test_result_logs(test_logs_path):
    test_results = {}
    
    # Verify input directory exists
    if not os.path.exists(test_logs_path):
        print(f"Error: Test logs file does not exist: {test_logs_path}")
        return test_results

    try:
        with open(test_logs_path, 'r', encoding='utf-8') as f:
            log_text = f.read()

        ## split based on "Entering: bug-"
        bug_sections = re.split(r'Entering: bug-', log_text)

        for section in bug_sections[1:]:  # Skip the first split as it won't contain a bug_id
            # Extract bug_id from the section Entering: bug-<Number>
            bug_id_match = re.search(r'(\d+)', section)
            if not bug_id_match:
                continue

            bug_id = "bug-" + bug_id_match.group(1)

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
        print(f"Error processing '{test_logs_path}': {e}")

    return test_results

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

def process_telemtery_logs(setting, gt_results, telemetry_log, output_csv_path, test_results=None):
    
    setting_path = f"Effectiveness_metrics/agent-logs/claude/agent-logs/claude/{setting}"
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
    for filename in os.listdir(telemetry_logs_dir):
        ## Process ONLY files ending with _telemetry.log
        if not filename.endswith(".txt"):
            continue

        input_filepath = os.path.join(telemetry_logs_dir, filename)
        
        try:
            with open(input_filepath, 'r', encoding='utf-8') as f:
                log_text = f.read()

            ### Note: This is a workaround because the Agent does not always produce any patches.
            ### So we need to check if the log contains string name='Edit'
            ### Step 1: Extract all the lines that contains name='Edit'
            edit_lines = re.findall(r".*name='Edit'.*", log_text)
            
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
            bug_id = filename.split("_output.txt")[0]
            
            if setting in ["Localized_With_No_Tests", "Non_Localized_With_No_Tests"]:
                repair_success = test_results.get(bug_id, {}).get("repair", 0)
                all_tests = test_results.get(bug_id, {}).get("all_tests", 0)
                passed_tests_after = test_results.get(bug_id, {}).get("passed_tests_after", 0)
                failed_tests_after = test_results.get(bug_id, {}).get("failed_tests_after", 0)
            else:
                passed_tests_after = 0
                failed_tests_after = 0
                
                ### === Results: 5 passed, 0 failed ===
                ### Search for the  last === Results: line and extract the numbers
                results_matches = re.findall(r'=== Results: (\d+) passed, (\d+) failed ===', log_text)
                if results_matches:
                    last_results_match = results_matches[-1]  # Get the last match
                    passed_tests_after = int(last_results_match[0])
                    failed_tests_after = int(last_results_match[1])

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

    telemetry_logs = ["logsLNT", "logsLT", "logsNLNT", "logsNLT"]
    

    for setting, telemetry_log in zip(settings, telemetry_logs):
        print(f"\n{'='*60}")
        print(f"Processing: {setting} / {telemetry_log}")
        print(f"{'='*60}")
        
        ## process ground truth patch files to get the modified java files for each bug_id
        gt_patch_dir = os.path.join("patches/merged_patches_final")
        gt_patch_files = process_gt_patch_java_files(gt_patch_dir)

        if setting in ["Localized_With_No_Tests"]:
            test_result_path = os.path.join("Effectiveness_metrics/agent-logs/claude", f"{setting}", "resultsLNT.txt")
            test_results = process_test_result_logs(test_result_path)
        if setting in ["Non_Localized_With_No_Tests"]:
            test_result_path = os.path.join("Effectiveness_metrics/agent-logs/claude", f"{setting}", "resultsNLNT.txt")
            test_results = process_test_result_logs(test_result_path)

        setting_path = f"Effectiveness_metrics/agent-logs/claude/{setting}"
        # Updated output path to save as a single CSV file
        output_csv_path = os.path.join(setting_path, f"{setting}_localisation_metrics.csv")

        process_telemtery_logs(setting, gt_patch_files, telemetry_log, output_csv_path, test_results)
        
