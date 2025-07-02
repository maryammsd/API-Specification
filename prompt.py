import requests
import json
from transformers import  AutoTokenizer

local_port = 11434     # Local port for forwarding

def set_local_port(port):
    global local_port
    local_port = port

def interact_with_deepseek(prompt):
    base_url = f"http://localhost:{local_port}/api/generate"
    data = {"model": "deepseek-r1:32b", "prompt": prompt}
    combined_response = ""
    try:
        response = requests.post(base_url, json=data, stream=False)
        #print("print print ")
        #print(response.status_code)
        after_think = False  # Flag to track when to start appending responses
        if response.status_code == 200:
            response_lines = response.text.strip().splitlines()
            for line in response_lines:
                if line.strip():  # Skip any empty lines
                    try:
                        json_obj = json.loads(line)
                        response_text = json_obj.get('response', '')
                         # Check if the line contains </think>
                        if "</think>" in response_text:
                            after_think = True  # Start appending responses after </think>
                            continue
                        if after_think:
                            combined_response += response_text
                        if json_obj.get('done', False):
                            break  # End of stream
                    except json.JSONDecodeError:
                        print(f"Warning: Could not parse line: {line}")
            #print(f"combined_response: {combined_response}")
            return combined_response.strip()  # Return the combined response string
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {e}"
    


def get_tokens_deepseek(string):
    #tokenizer = DeepSeekTokenizer()  # Create an instance of DeepSeekTokenizer
    #result = DeepSeekTokenizer.encode(text=string)

    chat_tokenizer_dir = "deepseek"
    tokenizer = AutoTokenizer.from_pretrained(chat_tokenizer_dir, trust_remote_code=True)
    result = tokenizer.encode(string)    
    return len(result)


def create_prompt_class(method, comment,prev_response):
    # Define the parameters for the completion
    # Define the parameters for the completion
    
    prompt = f"Imagine you are an Android developer expert. "\
             f" Here is the method {method}, and the comment that the user provide for it below: "\
             f" {comment}. "\
             f"Given this information, with the information you currently have predicted from the methods with @link in the comment, which is "\
             f" {prev_response},"\
             f" can you tell me what settings in an Android device should be configured for this method to operate correctly?"\
             f" Example 1: For method public boolean isProviderEnabledForUser, the below comment is given in the android source code"\
             f" comment description: Returns the current enabled/disabled status of the given provider. To listen for changes, see"\
             f" @link #PROVIDERS_CHANGED_ACTION. Before API version @link android.os.Build.VERSION_CODES#LOLLIPOP,"\
             f" this method would throw @link SecurityException if the location permissions were not sufficient to use"\
             f" the specified provider. "\
             f" @param provider a provider listed by @link #getAllProviders() "\
             f" @return true if the provider exists and is enabled "\
             f" previous response: For getAllProviders, the previous response says, there is no setting needed.  "\
             f" According to the comment and previous response, the following settings should be configured: "\
             f" Step 1. open android device settings."\
             f" Step 2. go to security and privacy."\
             f" Step 3. Ensure the app has the necessary permissions to access location services."\
             f" Step 4. Go back to the app settings and choose conneciton."\
             f" Step 5. Enable Wi-fi or Data connection."\
             f" Example 2: For the method public @NonNull List<String> getAllProviders(), the below comment is given in the android source code"\
             f" comment description: Returns a list of all providers that are available on the device. "\
             f" @return a list of all providers that are available on the device. "\
             f" previous response: <no response> as there is not @links to any method in the comment. "\
             f" According to the comment and previous response, no settings is required. "\
             f" Please follow the same format for the method and comment provided above."\
             f" Your output should be in the following format:"\
             f" Step 1. open android device settings."\
             f" Step 2. go to security and privacy."\
             f" Step 3. Ensure the app has the necessary permissions to access location services."\
             f" Or if no settings is required, just say no settings is required."
    return prompt

def create_prompt_method(method, comment):
    # Define the parameters for the completion
    # Define the parameters for the completion
    prompt = f"Imagine you are an Android developer expert. "\
             f" Here is the API {method}, and the comment that the user provide for it below: "\
             f" {comment}. "\
             f" can you tell me what settings in an Android device should be configured for this method to operate correctly?"\
             f" Example 1: For method public int getConnectionOwnerUid, given the comment below "\
             f" comment description: Returns the UID of the owner of the connection if the connection is found"\
             f" and the app has permission to observe it (e.g., if it is associated with the calling VPN app's tunnel) or -1 if the"\
             f" connection is not found."\
             f" resonse: Based on the above comment, the following steps should be perform to configure an Android deivce setting"\
             f" step 1. open android device setting. "\
             f" step 2. go to security and privacy and ensure the app has the necessary permissions to network."\
             f" Example 2: For the method public @NonNull List<String> getAllProviders(), the below comment is given in the android source code"\
             f" comment description: Returns a list of all providers that are available on the device. "\
             f" @return a list of all providers that are available on the device. "\
             f" According to the comment and previous response, no settings is required. "\
             f" Please follow the same format for the method and comment provided above."\
             f" Your output should be in the following format:"\
             f" Step 1. open android device settings."\
             f" Step 2. go to security and privacy."\
             f" Step 3. Ensure the app has the necessary permissions to access location services."\
             f" Or if no settings is required, just say no settings is required."
    return prompt

def merge_prompts(api_1,response1,previous_response,main_api):
    """
    Merges two prompts into one.
    """
    print("......................................................................")
    print("Merging prompts...")
    print(f"API 1: {api_1}")
    print(f"Response 1: {response1}")
    print(f"Previous Response: {previous_response}")
    prompt = f"Imagine you are an Android developer expert. "\
             f" You have predicted that"\
             f" {response1}"\
             f" is for operating the API {api_1}."\
             f" This API is accessed in {main_api} and we need "\
             f" {previous_response} to be configured."\
             f" If {api_1} is called in {main_api},"\
             f" can you predict the settings required for {main_api} to operate correctly?"\
             f" Your output should be in the following format:"\
             f" Step 1. open android device settings."\
             f" Step 2. go to security and privacy."\
             f" Step 3. Ensure the app has the necessary permissions to access location services."
    return prompt

def create_prompt_api_android_package_setting(package, version):
    # Define the parameters for the completion
    prompt = f"Imagine you are an Android developer expert. "\
             f" Can you estimate what configuration on an Android device setting affect"\
             f" calling a method from the class{package} in Android version {version} in an app's code ? "\
             f" Your answer must include the navigation to the required setting as shown the below examples: "\
             f" Example: For the API class android.Accessibility"\
             f" Navigate to Accessibility Settings: Step 1) Open setting on an Android device Step 2) Select Accessibility"\
             f" Step 3) Enable the specific accessibility service that your application provides (e.g., TalkBack, Switch Access, or any custom accessibility service you've developed)"\
             f" Example: For API class java.util.regex, no configuration in an Android device is needed. "\
             f" Just follow the above format and do not explain too much or make assumptions. Just answer based on the given information."
    return prompt

def check_similarity(response1, response2):
    prompt = f" Can you tell me if these two descriptions {response1} and {response2} for configuring an Android device"\
             f" are similar? Please perform cosine similarity checking and the output should be"\
             f" in format <output=value> where value is cosine simlarity you have calculated."
    return prompt