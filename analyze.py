import json
import pandas as pd
import prompt
import re
import logging


# Configure logging
logging.basicConfig(
    filename="result.log",  # Log file name in the current directory
    level=logging.INFO,          # Log level (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s"  # Log format
)

def message_log(message):
    logging.info(message)


def extract_output_value(response):
    """
    Extract the numeric value from a string in the format <output=0.5>.

    Args:
        response (str): The input string.

    Returns:
        float: The extracted numeric value, or None if not found.
    """
    match = re.search(r"<output=([0-1](?:\.\d+)?)>", response)
    if match:
        return float(match.group(1))  # Extract and convert the value to a float
    return None


def check_similarity(json_result,excel_result,node_value):
    prompt_ = prompt.check_similarity(excel_result,json_result)
    response = prompt.interact_with_deepseek(prompt_)
    print(f" the similarity is {response}")
    value = extract_output_value(response)
    if value is not None:
        if value >= 0.5 :
            print(f"Node '{node_value}': Results match.")
        else:
            print(f"Node '{node_value}': Results do not match.")
            print(f"  JSON Result: {json_result}")
    return value

def check_no_setting(response):
    response_lower = str(response).lower()
    if "no setting" in response_lower:
        return True
    if "no additional setting" in response_lower:
        return True
    if "no additional device setting" in response_lower:
        return True
    if "no specific device setting" in response_lower:
        return True
    if "no specific Android device settings" in response_lower:
        return True
    if "no further device setting" in response_lower:
        return True
    return False

def compare_json_with_excel(json_file_path, excel_file_path):
    """
    Compare node values and results from a JSON file with an Excel file.

    Args:
        json_file_path (str): Path to the JSON file.
        excel_file_path (str): Path to the Excel file.

    Returns:
        None
    """
    try:
        # Load the JSON file
        with open(json_file_path, "r") as json_file:
            json_data = [json.loads(line) for line in json_file]

         # Filter elements where 'node' starts with 'android.'
        matching_elements = [item for item in json_data if item.get("node", "").startswith("android.")]

        # Load the Excel file
        excel_data = pd.read_excel(excel_file_path)
        match_count = 0
        not_match_count = 0
        not_found = 0
        result = {}
        # Iterate through each node in the JSON file
        for item in matching_elements:
            node_value = item.get("node", "")
            json_result = item.get("response", "")
            response_t = item.get("response_token","")
            prompt_t = item.get("prompt_token","")

            # Check if the node exists in the Excel file
            matching_row = excel_data[excel_data.iloc[:, 0] == node_value]  # First column contains node values
            value = 0
            if not matching_row.empty:
                # Node exists in the Excel file
                excel_result = matching_row.iloc[0, 4]  # 5th column contains the result
                excel_prompt_t = matching_row.iloc[0, 2]  # 3rd column
                excel_response_t = matching_row.iloc[0, 3]  # 4th column

                match_count = match_count+1
                if check_no_setting(excel_result) and check_no_setting(json_result):
                    value =  1.0
                else:
                    value = check_similarity(json_result,excel_result,node_value)
                result[node_value] = {
                    "similarity": value,  # Replace with actual value
                    "response": response_t,  # Replace with actual value
                    "prompt": prompt_t,  # Replace with actual value
                    "a_response": excel_response_t,  # Replace with actual value
                    "a_prompt": excel_prompt_t   # Replace with actual value
                }
                message_log(f"{node_value},{value},{prompt_t},{response_t},{excel_prompt_t},{excel_response_t}")
            else:
                # Node does not exist in the Excel file
                #print(f"Node '{node_value}' not found in Excel. Generating prompt...")
                # Generate a prompt and get the result (placeholder for actual prompt generation logic)
                generated_result = prompt.create_prompt_api_android_package_setting(node_value,"35")
                response = prompt.interact_with_deepseek(generated_result)
                mysolution_response_t = prompt.get_tokens_deepseek(response)
                mysolution_prompt_t = prompt.get_tokens_deepseek(generated_result)
                if check_no_setting(mysolution_response_t) and check_no_setting(json_result):
                    value =  1.0
                else:
                    value = check_similarity(json_result,generated_result,node_value)
                result[node_value] = {
                    "similarity": value,  # Replace with actual value
                    "response": response_t,  # Replace with actual value
                    "prompt": prompt_t,  # Replace with actual value
                    "a_response": mysolution_response_t,  # Replace with actual value
                    "a_prompt": mysolution_prompt_t   # Replace with actual value
                }
                message_log(f"{node_value},{value},{prompt_t},{response_t},{mysolution_prompt_t},{mysolution_response_t}")
            
        print(f"matched {match_count} and not matched {not_match_count}")
        print(f"not found {not_found}")
        total_similar = 0
        total_response_sp = 0
        total_request_sp = 0
        total_response_mysolution = 0
        total_request_mysolution = 0
        count = 0

        for key, value in result.items():
            if "similarity" in value:  # Check if found correctly
                if value["similarity"] >= 0.5:
                    total_similar += 1
            if "response" in value:  # Check if found correctly
                total_response_sp += value["response"]
            if "prompt" in value:  # Check if found correctly
                total_request_sp += value["prompt"]
            if "a_response" in value:  # Check if found correctly
                total_response_mysolution += value["a_response"]
            if "a_prompt" in value:  # Check if found correctly
                total_request_mysolution += value["a_prompt"]
            count += 1
        print(f" Total number of elements {count}")
        print(f" Average my solution prompt {total_request_mysolution} response {total_response_mysolution}")
        print(f" Average specification inference prompt {total_request_sp} response {total_response_sp}")
        print(f" Total number of elements {count}")
        message_log(f"Total {count} API classes")
        message_log(f" Average my solution prompt {total_request_mysolution/count} response {total_response_mysolution/count}")
        message_log(f" Average specification inference prompt {total_request_sp/count} response {total_response_sp/count}")

    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def is_number(value):
    try:
        float(value)  # Try to convert to float
        return True
    except ValueError:
        return False
    
def read_result_logs(file_path):
    total_similar = 0
    total_different = 0
    total_response_sp = 0
    total_request_sp = 0
    total_response_mysolution = 0
    total_request_mysolution = 0
    count = 0
    
    with open(file_path,"r") as file:
        for line in file:
            values = []
            if "INFO -" in line:
                value_after_info = line.split("INFO -", 1)[1].strip()
                # Split the extracted value by commas
                values = value_after_info.split(",")
                if len(values) >= 6:
                    count += 1
                    if values[1] is not None and is_number(values[1]):
                        if float(values[1]) >= 0.6:
                            total_similar += 1
                        else:
                            total_different += 1
                    total_request_sp += float(values[2])
                    total_response_sp += float(values[3])
                    total_response_mysolution += float(values[4])
                    total_request_mysolution += float(values[5])
                else:
                    print(f"Error! number of elements in the line is {len(values)}")
    print(f" Total number of different elements {total_different}")
    print(f" Total number of similar elements {total_similar}")
    print(f" Total number of elements {count}")
    print(f" Average my solution prompt {total_request_mysolution/count} response {total_response_mysolution/count}")
    print(f" Average specification inference prompt {total_request_sp/count} response {total_response_sp/count}")



def generate_prompt_result(node_value):
    """
    Generate a result for a node value (placeholder for actual prompt logic).

    Args:
        node_value (str): The node value.

    Returns:
        str: The generated result.
    """
    # Placeholder logic for generating a result
    return f"Generated result for {node_value}"

# Example usage
json_file_path = "/home/maryam/clearblue/java-code/py-code/response_log.json"
excel_file_path = "/home/maryam/clearblue/java-code/py-code/functions/static-class-gpt.xlsx"
log_file_path =  "/home/maryam/clearblue/java-code/py-code/result.log"
compare_json_with_excel(json_file_path, excel_file_path)
read_result_logs(log_file_path)