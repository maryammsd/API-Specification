# Android API Specification

This project is designed to analyze and visualize class dependencies and relationships in Android codebases. It builds a directed graph from JSON files representing class structures and their members, processes links between classes and members, and provides various insights into the graph.

## Features

- **Graph Construction**: Builds a directed graph from JSON files representing class structures and their members.
- **Visualization**: Generates both static (`.png`) and interactive (`.html`) visualizations of the graph.
- **Graph Analysis**:
  - Calculates graph depth and number of nodes.
  - Identifies isolated nodes.
  - Detects cycles.
  - Finds top dependencies (classes with maximum and minimum dependencies).
- **Integration with DeepSeek**: Interacts with DeepSeek for processing node comments in order to analyze the comments from dependent methods to geneate a description of steps to configure. A *step to configure (s2r)* declares the steps to configure an Android device for an API class or method to operate when being called in an app code. 

## Project Structure

```
deepseek/ 
functions/
main.py
prompt.py
```

### Key Files

- **`main.py`**: The main script for graph construction, visualization, and analysis.
- **`prompt.py`**: Handle interaction with LLM.
- **`function/`**: Contains an excel file consisting of the list of API classes. The result of the analysis will be stored under this directory for further notice. 

## Usage

After installing required packages, you can run the code by,
````
python main.py
````
There are four different operations you can perform,
````
1. Read from Excel file and build the graph for each class (if not exists), then interact with LLM to find dependencies.
2. Specify the path of excel file consisting of the list of classes. 
3. Enter a class name and find its dependencies.
4. exit

````
If you choose operation 3, you must enter the API class method with its package name (example: `android.io.Bundle`). 

Remember to modify the below variables in function `main` in the `main.py` before running the code,

````
- output_json_dir = "PATH_TO_JSON-FILES" : `PATH_TO_JSON-FILES` points to the directory where the `json` files consisting of information about the methods and variables dependent to each other for a class. These files are generated after running the project available here. 
- output_excel_dir = "PATH_TO_EXCEL_FILE" : `PATH_TO_EXCEL_FILE` points to the file that consists of list of class names in its first column, that we want to predict the Android device settings for them.
- output_graph_dir = "PATH_TO_GRAPH_FILES": `PATH_TO_GRAPH_FILES` points to the directory where the graph representation of `json` files in `PATH_TO_JSON-FILES` are kept. 

````

### Outputs

- **Interactive Visualization**: `<Android API CLASS NAME>.html`
- **Graph Data**: `<Android API CLASS NAME>.gml`
- **Specification**: `response_log.json`

### Graph Analysis

The script provides operations such as:
- Budiling the graph of dependency between methods and classes for a specific Android API class. 
- Information about the graph such as the 
  - Number of nodes and edges.
  - Depth of the graph.
  - Isolated nodes.
  - Top dependencies.
- Interacting with LLM to predict settings by traversing the dependency graph. 
  - Connection to DeepSeek-r1:32 through ollama on our remote server. 
  - Prompt template for inferring the Android device setting given the method dependencies with comments.


## Dependencies

- Python 3.x
- NetworkX
- Matplotlib
- PyVis
- Pandas

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License.

## Contact

For questions or support, please contact [Maryam](mailto:mamt@connect.ust.hk).