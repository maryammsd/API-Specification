import os
import json
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
from prompt import prompt  # Assuming you have a prompt module for generating prompts

def read_excel_file(file_path):
    """
    Read the Excel file and extract class names from the first column.
    """
    df = pd.read_excel(file_path)
    class_names = df.iloc[:, 0].dropna().tolist()  # Get the first column and drop NaN values
    return class_names

def find_class_file(output_dir, class_name):
    """
    Search for the JSON file corresponding to the given class name in the output directory.
    """
    file_name = f"{class_name}.json"
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file == file_name:
                return os.path.join(root, file)
    return None

def build_graph(output_dir, links, graph=None, visited_links=None, parent_class=None):
    """
    Build a graph of @link references.
    """
    if graph is None:
        graph = nx.DiGraph()  # Directed graph
    if visited_links is None:
        visited_links = set()

    for link in links:

        if link in visited_links:
            print(f"Link {link} already visited, skipping.")
            continue
        visited_links.add(link)

        # Check if the link is a class or a class#member reference or a #member reference
        member_name = None
        if parent_class is None:
            if "#" in link:
                parent_class, member_name = link.split("#")
            else:
                parent_class = link
       

        class_file = find_class_file(output_dir, parent_class)
        if class_file is None:
            print(f"Class file not found for {parent_class}")
            continue
        else:
            # Process the class file
            print(f"Processing class: {parent_class}")
            with open(class_file, "r") as f:
                data = json.load(f)

            # Check if the class has already been added to the graph
            if not graph.has_node(parent_class):
                # Add the class node
                graph.add_node(parent_class, type="class", comment=data.get("comment"))
                # Process variables and methods
                #process_members(data.get("variables", []), parent_class, graph, visited_links, output_dir, "variable")
                print(f"Processing methods in class: {parent_class}")
                methods = data.get("methods", [])
                print(f"Found {len(methods)} methods in class {parent_class}")
                process_members(methods, parent_class, graph, visited_links, output_dir, "method")
            else:
                print(f"Class {parent_class} already exists in the graph, skipping.")

    return graph


def process_members(members, parent_class, graph, visited_links, output_dir, member_type):
    """
    Process variables or methods and add them to the graph.
    """
    # length of members
    print(f"Processing {len(members)} {member_type}s in class {parent_class}")
    for member in members:
        member_name = member.get("name")
        print(f"Processing member: {member_name} of type {member_type} in class {parent_class}")
        if member_name is None:
            continue
        # Check if the member is already visited
        if f"{parent_class}#{member_name}" in visited_links:
            print(f"Member {member_name} already visited, skipping.")
            continue
        visited_links.add(f"{parent_class}#{member_name}")

        # Add the member node
        if member.get("comment") is not None:
            if member.get("comment") != "" and "@hide" not in member.get("comment") and "@deprecated" not in member.get("comment")  and "@remove" not in member.get("comment"):
                if member_type == "method":
                    print(f"Processing method: {member_name} in class {parent_class}")
                    if not graph.has_node(member_name):
                        graph.add_node(member_name, type=member_type, comment=member.get("comment"))
                    else:
                        graph.nodes[member_name]["comment"] = member.get("comment")
                        graph.nodes[member_name]["type"] = member_type
                    if not graph.has_edge(parent_class, member_name):
                        graph.add_edge(parent_class, member_name, type="child")
                    #print(f"Added edge from {parent_class} to {member_name} ({member_type}).")
                elif member_type == "variable" or member_type == "link-shadow":
                    if graph.has_node(member_name):
                        print(f"Node {member_name} already exists, and removing it .")
                        graph.remove_node(member_name)  # Remove the existing node if it exists
                # Process links
                #if member_type == "method":
                process_links(member_name, parent_class, member.get("links", []), graph, visited_links, output_dir)


def process_links(member_name,parent_class, links, graph, visited_links,output_dir):
    """
    Process links for a member and add edges to the graph.
    """
    for link in links:
        print(f"Processing link: {link} for member {member_name}")
        target_name ,child_name =  get_names_from_link(link, parent_class)
        # case 1) target_name is None and child_name is None
        if child_name is None and target_name is None:
            #print(f"Invalid link: {link} for member {member_name}")
            continue
        if target_name is None or target_name == "":
            # If target_name is None, it means the link is a member in the same class
            #print(f"Link {link} is invalid, skip it .")
            continue
        # If target_name is not None, it can be one of the following:
        # case 2) target_name equals to member_name
        # case 3) target_name is not equal to member_name
        if child_name == "":
            # If child_name is empty, it means the link is a class without a member
            if graph.has_node(target_name):
                print(f"Target class {target_name} exists, adding it as a link.")
                # Add the target class as a link
                graph.add_edge(member_name, target_name, type="link")
            else:
                build_graph(output_dir, [target_name], graph, visited_links)
                # Add the target class as a link
                graph.add_edge(member_name, target_name, type="link")
            continue
        
        if target_name == parent_class:
            # If target_name is the same as parent_class, it means the link is a member in the same class
             if not graph.has_node(child_name):
                #print(f"Target node {target_name} exists, adding child node {child_name} as a link.")
                # Add the child node as a link
                graph.add_node(child_name, type="link-shadow", comment="No comment available")
        elif target_name != parent_class:
            # If target_name is not the same as parent_class, it means the link is a member in another class
            print(f"Link {link} is a member in another class: {target_name}")
            # Check if the target class exists in the graph
            if not graph.has_node(target_name):
                #print(f"Target class {target_name} does not exist, building graph for it.")
                graph.add_node(child_name, type="link-shadow", comment="No comment available")
                build_graph(output_dir, [target_name], graph, visited_links)
            #else:
                #print(f"Target class {target_name} already exists in the graph.")
        if graph.has_node(child_name) and not graph.has_edge(member_name, child_name):
            #print(f"Adding edge from {member_name} to {child_name} (link).")
            graph.add_edge(member_name, child_name, type="link")
        elif child_name != "" and child_name is not None:
            if graph.has_edge(member_name, target_name):
                # If the edge already exists, skip adding it
                print(f"Edge from {member_name} to {target_name} already exists, skipping.")
            else:
                graph.add_edge(member_name, target_name, type="link")
                print(f"Edge from {member_name} to {child_name} added.")  

        # Add the link to the graph
          
        
        
    
def get_names_from_link(link, parent_class):
    """
    Extract the child and parent names from the link.
    """
    child_name = None
    target_name = None
    if link.startswith("#"):
        # Case 1: #member (member in the same class)
        target_member = link[1:]  # Remove the leading '#'
        child_name = target_member
        target_name = parent_class
    elif '#' in link:
        # Case 2: class#member (member in another class)
        parts = link.split('#')
        target_name = parts[0]  # Get the class name before the '#'
        child_name = parts[1]  # Get the member name after the '#'
    else:
        # Case 3: class (class without member)
        child_name = ""  # No specific member, just the class
        target_name = link

    return target_name, child_name


def visualize_graph(graph, output_file="graph.png"):
    """
    Visualize the graph and save it as an image.
    """
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(graph)
    nx.draw(
        graph,
        pos,
        with_labels=True,
        node_size=2000,
        node_color="lightblue",
        font_size=10,
        font_color="black",
        edge_color="gray",
    )
    plt.title("Graph of @link References")
    plt.savefig(output_file)  # Save the graph as an image
    plt.show()

def read_function_list(file_path):
    """
    Read the function_list.txt file and parse the class and function names.
    """
    functions = []
    with open(file_path, "r") as f:
        for line in f:
            #print(f"Processing line: {line.strip()}")
            parts = line.strip().split(',')
            if len(parts) == 2:
                class_package, function_name = parts
                functions.append((class_package, function_name))
    return functions

def find_function_in_json(output_dir, class_package, function_name):
    """
    Search for a specific function in the JSON files in the output directory.
    """
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".json"):
                json_path = os.path.join(root, file)
                with open(json_path, "r") as f:
                    try:
                        data = json.load(f)
                        # Check if the class matches the given package
                        # Get class name from the file name
                        class_name = data.get("className", "")
                        package_class = f"{data.get('packageName', '')}.{class_name}"
                        if package_class == class_package:
                            #print(f"Found class: {package_class} in file: {json_path}")
                            # Search for the function in the methods list
                            for method in data.get("methods", []):
                                if method.get("name") == function_name:
                                    return method, data
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON file: {json_path}")
    return None, None


def get_number_of_nodes(graph):
    """
    Get the number of nodes in the graph.
    """
    num_nodes = graph.number_of_nodes()
    print(f"Number of nodes in the graph: {num_nodes}")
    return num_nodes

def visualize_interactive(graph, output_file="graph.html"):
    net = Network(notebook=True, directed=True)
    for node, data in graph.nodes(data=True):
        net.add_node(node, label=node, title=str(data))
    for source, target, data in graph.edges(data=True):
        net.add_edge(source, target, title=str(data))
    net.show(output_file)


def get_graph_depth(graph):
    """
    Calculate the depth of the graph (longest path), considering cycles.
    """
    try:
        if nx.is_directed_acyclic_graph(graph):
            # If the graph is a DAG, use the built-in method
            depth = nx.dag_longest_path_length(graph)
            print(f"Depth of the graph (DAG): {depth}")
            return depth
        else:
            # Handle graphs with cycles
            print("The graph contains cycles. Calculating depth by ignoring cycles.")
            # Convert the graph to an undirected graph to ignore cycles
            undirected_graph = graph.to_undirected()
            # Find the longest path using connected components
            longest_path_length = 0
            for component in nx.connected_components(undirected_graph):
                subgraph = graph.subgraph(component)
                # Use all-pairs shortest path to approximate the longest path
                lengths = nx.all_pairs_shortest_path_length(subgraph)
                for _, length_dict in lengths:
                    longest_path_length = max(longest_path_length, max(length_dict.values()))
            print(f"Approximate depth of the graph (with cycles): {longest_path_length}")
            return longest_path_length
    except Exception as e:
        print(f"Error calculating graph depth: {e}")
        return None

def find_class_dependencies(graph):
    """
    Find dependencies for each class in the graph.
    """
    class_dependencies = {}

    for node, data in graph.nodes(data=True):
        dependencies = [target
            for _, target, edge_data in graph.out_edges(node, data=True)
        ]
        class_dependencies[node] = dependencies

    return class_dependencies

def make_graph_acyclic(graph):
    """
    Convert a cyclic graph into an acyclic graph by removing redundant links.
    """
    try:
        # Check if the graph is already a DAG
        if nx.is_directed_acyclic_graph(graph):
            print("The graph is already acyclic.")
            return graph

        print("The graph contains cycles. Removing redundant links to make it acyclic.")
        
        # Find cycles in the graph
        cycles = list(nx.simple_cycles(graph))
        print(f"Found cycles: {cycles}")

        # Remove edges that create cycles
        for cycle in cycles:
            # Remove one edge from each cycle to break it
            for i in range(len(cycle)):
                source = cycle[i]
                target = cycle[(i + 1) % len(cycle)]  # Next node in the cycle
                if graph.has_edge(source, target):
                    print(f"Removing edge {source} -> {target} to break the cycle.")
                    graph.remove_edge(source, target)
                    break  # Break only one edge per cycle

        print("Graph has been converted to acyclic.")
        return graph
    except Exception as e:
        print(f"Error while making graph acyclic: {e}")
        return graph

def find_top_dependencies(class_dependencies, top_n=5):
    """
    Find the top N elements with the maximum and minimum dependencies.
    """
    # Sort by the number of dependencies
    sorted_dependencies = sorted(class_dependencies.items(), key=lambda x: len(x[1]), reverse=True)

    # Get top N elements with maximum dependencies
    max_dependencies = sorted_dependencies[:top_n]

    # Get top N elements with minimum dependencies
    min_dependencies = sorted_dependencies[-top_n:]

    print(f"Top {top_n} elements with maximum dependencies:")
    for class_name, dependencies in max_dependencies:
        print(f"{class_name}: {len(dependencies)} dependencies")
        for dep in dependencies:
            print(f"  - {dep}")
    zero_dep = 0
    one_dep = 0
    for class_name, dependencies in sorted_dependencies:
        if len(dependencies) == 0:
            print(f"{class_name} has no dependencies.")
            zero_dep += 1
        if len(dependencies) == 1:  
            one_dep += 1
    print(f"Number of classes with no dependencies: {zero_dep}")
    print(f"Number of classes with one dependency: {one_dep}")
    for class_name, dependencies in min_dependencies:
        print(f"{class_name}: {len(dependencies)} dependencies")

    return max_dependencies, min_dependencies

def build_graph_initiate(links,output_dir):
      # Build the graph
    graph = build_graph(output_dir, links)
    #for node, data in graph.nodes(data=True):
        #for key, value in data.items():
            #if value is None:
                #print(f"Node {node} has a None value for attribute {key}")
    # remove all edges with type variable
    edges_to_remove = [(source, target) for source, target, data in graph.edges(data=True) if data.get("type") == "variable"]
    graph.remove_edges_from(edges_to_remove)
    #for source, target, data in graph.edges(data=True):
        #for key, value in data.items():
            #if value is None:
                #print(f"Edge {source} -> {target} has a None value for attribute {key}")
    
    visualize_graph(graph, "class_graph.png")
    visualize_interactive(graph, "class_graph.html")

    #graph = make_graph_acyclic(graph)  # Convert to acyclic graph if needed
    # Visualize the graph
    #visualize_graph(graph, "class_graph_acyclic.png")
   # visualize_interactive(graph, "class_graph_acyclic.html")

    # Save the graph to a file (optional)
    nx.write_gml(graph, "class_graph.gml")  # Save in GML format for visualization

    # Print graph information
    print(f"Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")
    print("Nodes:")
    for node, data in graph.nodes(data=True):
        print(f"{node}: {data}")
    print("Edges:")
    for source, target, data in graph.edges(data=True):
        print(f"{source} -> {target}: {data}")
     # Calculate depth and number of nodes
    depth = get_graph_depth(graph)
    num_nodes = get_number_of_nodes(graph)

    # Print results
    isolated_nodes = list(nx.isolates(graph))
    print(f"Isolated nodes: {isolated_nodes}")
    print(f"Graph Depth: {depth}")
    print(f"Number of Nodes: {num_nodes}")
    # print total numbder of edges
    print(f"Total number of edges in the graph: {graph.number_of_edges()}")
    # print total number of paths from root to leaf nodes
    #print(f"Total number of paths from root to leaf nodes: {nx.number_of_simple_paths(graph)}")
    # print if the graph is a DAG
    print(f"Graph is directed: {graph.is_directed()}")
    print(f"Graph is undirected: {graph.is_directed() is False}")
    print(f"Graph is connected: {nx.is_connected(graph.to_undirected())}")
    print(f"Graph is weakly connected: {nx.is_weakly_connected(graph)}")
    print(f"Graph is strongly connected: {nx.is_strongly_connected(graph)}")
    print(f"Graph has cycles: {nx.is_directed_acyclic_graph(graph) is False}")
    print(f"Graph has self loops: {nx.number_of_selfloops(graph)}")
    print(f"Graph has multiple edges: {nx.number_of_edges(graph) > graph.number_of_nodes() - 1}")
    print(f"Graph has parallel edges: {nx.number_of_edges(graph) > graph.number_of_nodes() - 1}")
    print(f"Graph has isolated nodes: {len(list(nx.isolates(graph))) > 0}")
    print(f"Graph has isolated edges: {len(list(nx.isolates(graph.to_undirected()))) > 0}")
    print(f"Is the graph a DAG (Directed Acyclic Graph)? {nx.is_directed_acyclic_graph(graph)}")

    #Find top dependencies
    top_max, top_min = find_top_dependencies(find_class_dependencies(graph), top_n=5)
    print(f"Top dependencies (max): {top_max}")
    print(f"Top dependencies (min): {top_min}")
    return graph


def traverse_from_leaves_to_roots_with_cycles(graph):
    """
    Traverse a graph from leaves to roots, handling cycles, and pass results to predecessors.

    Args:
        graph: A NetworkX graph object.
        operation: A function to perform on each node. It should accept the node and its results from successors.

    Returns:
        node_results: A dictionary mapping each node to its result.
    """
    # Step 1: Connect to the deepseek server 

    # Step 2: Initialize results dictionary
    node_results = {}
    visited_nodes = set()  # To keep track of visited nodes
    processing_nodes = set()  # To track nodes currently being processed

    
    # Step 5: Compute results for all nodes starting from leaf nodes
    node = next(iter(graph.nodes)) # Get one node from the reversed graph
    compute_result(node,node_results,graph,visited_nodes,processing_nodes)
    # Get the next node to process
       
    return node_results


# Step 4: Define a helper function for dynamic programming
def compute_result(node,node_results,graph,visited_nodes,processing_nodes):
   
    if node in processing_nodes:
        print(f"Node {node} has already been visited, using cached value.")
        return
    
    # Mark the node as being processed
    processing_nodes.add(node)

    # If the result for the current node is already computed, return it
    if graph.out_degree(node) == 0:
        print(f"Node {node} is a leaf node, returning its value.")
        if node.get("comment") is not None and node.get("comment") != "" and node.get("comment") != "No comment available":
            # If the node has a comment, create a prompt and interact with DeepSeek
            prompt = prompt.create_prompt_method(node, graph.nodes[node].get("comment", ""))
            response = prompt.interact_with_deepseek(prompt)
            node_results[node] = str(response)
            # add code for logging the response and the number of tokens and run-time infomrmation
        else :
            # If the node has no comment, return its name
            node_results[node] = ""
        visited_nodes.add(node)  # Mark the node as visited
        #processing_nodes.remove(node)
        return
    
    
    print(f"Computing result for node: {node}")

    successors_results = []
    for successor in graph.successors(node):  # Ensure `node` is a valid identifier
        if successor not in node_results and successor not in processing_nodes:            
            compute_result(successor, node_results, graph, visited_nodes, processing_nodes)
            successors_results.append(node_results[successor])

    # Merge successor results and compute the current node's value
    for result in successors_results:
        if result is None or result == "":
            continue
        prompt = prompt.create_prompt_class(node, result)
        response = prompt.interact_with_deepseek(prompt)
        if response is None or response == "":
            print(f"Response for node {node} is None or empty, skipping.")
            continue
        node_results[node] = str(response)
    node_results[node] = str(node) + " -> " + ", ".join(successors_results)
    visited_nodes.add(node)  # Mark the node as visited
    #processing_nodes.remove(node)  # Remove the node from processing set

    
 

def main():
    # Paths
    output_dir = "/home/maryam/clearblue/java-code/java-code/output"
    links = [
        # Example links to process
        "android.telephony.TelephonyManager"
    ]
    graph = build_graph_initiate(links, output_dir)
    if graph is None:
        print("No graph was built. Exiting.")
        graph = nx.DiGraph()
        graph.add_edges_from([
            ("A", "B"),
            ("B", "C"),
            ("C", "A")
        ])

    node_results = traverse_from_leaves_to_roots_with_cycles(graph)
    for node in node_results:
        if node == links[0]:
            print(f"Root node: {node}")
            for item in node_results[node].split(' -> '):
                print(f"Root node link: {item}")
            print(f"Number of Links: {len(node_results[node].split(' -> ')) - 1}")
        print(f"Node: {node}, Result: {node_results[node]}")

  
    
    # Find dependencies for each class
    #class_dependencies = find_class_dependencies(graph)

    # Print dependencies
    #for class_name, dependencies in class_dependencies.items():
    #    if dependencies:
    #        print(f"element: {class_name}")
    #        print(f"Depends on: {dependencies}")

if __name__ == "__main__":
    main()