import json

# Filepath to your JSON file
file_path = "response_log_gpt.json"

# Load the JSON file as a single array
with open(file_path, "r") as file:
    try:
        data = json.load(file)  # Load the entire JSON array
    except json.JSONDecodeError as e:
        print(f"Error loading JSON file: {e}")
        data = []

# Use a set to track unique (parent, node) pairs
unique_entries = set()
cleaned_data = []

# Iterate through the JSON data
for entry in data:
    parent = entry.get("parent")
    node = entry.get("node")
    # Check if the (parent, node) pair is unique
    if (parent, node) not in unique_entries:
        unique_entries.add((parent, node))
        cleaned_data.append(entry)

file_path = "response_log_deepseek_new.json"
# Save the cleaned data back to the file
with open(file_path, "w") as file:
    json.dump(cleaned_data, file, indent=4)

print(f"Duplicates removed. Cleaned data saved to {file_path}.")