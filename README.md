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
- **Dynamic Traversal**: Traverses the graph from leaves to roots, handling cycles dynamically and try to extract the specification for each API class.
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
- **`function/`**: Contains an excel file consisting of the list of API classes. The result of the analysis will be stored under this directory for further notice. 
- **`py-code/`**: Contains Python scripts for processing and analysis.

## Usage

### Build and Visualize Graph

Run the `main.py` script to build and visualize the graph:
```bash
python main.py
```

### Example Input

The script processes links like:
```python
links = [
    "android.telephony.TelephonyManager"
]
```

### Outputs

- **Static Visualization**: `class_graph.png`
- **Interactive Visualization**: `class_graph.html`
- **Graph Data**: `class_graph.gml`
- **Specification**: `class-spec.xlsx`

### Graph Analysis

The script provides insights such as:
- Number of nodes and edges.
- Depth of the graph.
- Isolated nodes.
- Top dependencies.
- Prompts for inferring the Android device setting given the method dependencies with comments.

### Dynamic Traversal

The script traverses the graph dynamically, handling cycles and interacting with DeepSeek for node processing.

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