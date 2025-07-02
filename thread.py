import threading
import requests
import json

def send_request_to_deepseek(prompt, url="http://localhost:11434/api/generate"):
    """
    Send a request to the DeepSeek server with the given prompt.
    """
    data = {"model": "deepseek-r1:32b", "prompt": prompt}
    try:
        response =requests.post(url, json=data, stream=False)
        after_think = False

        if response.status_code == 200:
            response_lines = response.text.strip().splitlines()
            combined_response = ""
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
            print(f"combined_response: {combined_response}")
            return combined_response.strip()  # Return the combined response string
        else:
            print(f"Error for prompt '{prompt}': {response.status_code}")
    except Exception as e:
        print(f"Error sending request for prompt '{prompt}': {e}")

def main():
    # List of prompts to send
    prompts = [
        "What are the settings for Node A?",
        "What are the settings for Node B?",
        "What are the settings for Node C?",
        "What are the settings for Node D?",
        "What are the settings for Node E?"
    ]
    send_request_to_deepseek("What are the settings for Node A?")
    # Create threads for each prompt
    threads = []
    for prompt in prompts:
        thread = threading.Thread(target=send_request_to_deepseek, args=(prompt,))
        threads.append(thread)

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    print("All requests have been processed.")

if __name__ == "__main__":
    main()