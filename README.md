# Android API Specification

This project is designed to analyze and visualize class dependencies and relationships in Android codebases. It builds a directed graph from JSON files representing class structures and their members, processes links between classes and members, and provides various insights into the graph.

## Features

- **Graph Construction**: Builds a directed graph from JSON files representing class structures and their members.
- **Visualization**: Generates both static (`.png`) and interactive (`.html`) visualizations of the graph.
- **Graph Analysis**:
  - Calculates graph depth and number of nodes.
  - Identifies isolated nodes.
  - Detects cycles and converts cyclic graphs into acyclic graphs.
  - Finds top dependencies (classes with maximum and minimum dependencies).
- **Dynamic Traversal**: Traverses the graph from leaves to roots, handling cycles dynamically.
- **Integration with DeepSeek**: Interacts with DeepSeek for processing node comments.

## Project Structure

```
callgraph-2.json
callgraph-layer-2.json
.vscode/
artifacts/
files/
java-code/
report/
source-code/
tar-files/
```

### Key Files

- **`main.py`**: The main script for graph construction, visualization, and analysis.
- **`artifacts/`**: Contains intermediate files generated during processing.
- **`java-code/py-code/`**: Contains Python scripts for processing and analysis.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd clearblue
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

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

### Graph Analysis

The script provides insights such as:
- Number of nodes and edges.
- Depth of the graph.
- Isolated nodes.
- Top dependencies.

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