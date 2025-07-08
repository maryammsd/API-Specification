import pandas as pd
from io import StringIO

# Function to calculate min, max, average, and median
def calculate_stats(series):
    return {
        'Min': series.min(),
        'Max': series.max(),
        'Average': series.mean(),
        'Median': series.median()
    }


def read_results(result_path):
    # Read the data from the .txt file
    with open(result_path, 'r') as file:
        data = file.read()

    # Read the data into a DataFrame
    df = pd.read_csv(StringIO(data), header=None)

    # Rename columns for clarity
    df.columns = ['Package Name', 'Issue ID', 'Setting', 'Reachable Variables', 'Total Variables', 
                'Reachable Statements', 'Total Statements', 'Reachable Methods', 'Total Methods']

    # Calculate rates
    df['Variable Rate'] = df['Reachable Variables'] / df['Total Variables'].replace(0, 1)  # Avoid division by zero
    df['Statement Rate'] = df['Reachable Statements'] / df['Total Statements'].replace(0, 1)
    df['Method Rate'] = df['Reachable Methods'] / df['Total Methods'].replace(0, 1)

    # Select relevant columns for Markdown table
    markdown_table = df[['Package Name', 'Issue ID', 'Setting', 
                        'Variable Rate', 'Statement Rate', 'Method Rate']]

    # Convert to Markdown format
    markdown_str = markdown_table.to_markdown(index=False)

    # Print Markdown table
    print(markdown_str)
    # Calculate statistics for each rate
    variable_stats = calculate_stats(df['Variable Rate'])
    statement_stats = calculate_stats(df['Statement Rate'])
    method_stats = calculate_stats(df['Method Rate'])

    # Print the results
    print("Variable Rate Statistics:", variable_stats)
    print("Statement Rate Statistics:", statement_stats)
    print("Method Rate Statistics:", method_stats)


result_path = "/home/maryam/clearblue/java-code/py-code/functions/static-result.txt"
read_results(result_path)