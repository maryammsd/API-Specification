import os
import json
import time
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import prompt  # Assuming you have a prompt module for generating prompts

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

import os
import networkx as nx

def save_graph_to_gml(graph, output_dir, file_name):
    """
    Save the graph to a .gml file in the specified directory.

    Args:
        graph: The NetworkX graph object.
        output_dir: The directory where the .gml file should be saved.
        file_name: The name of the .gml file.
    """
    # Ensure the directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # Create the directory if it doesn't exist

    # Construct the full path for the .gml file
    graph_path = os.path.join(output_dir, file_name)

    # Save the graph to the .gml file
    nx.write_gml(graph, graph_path)
    print(f"Graph saved to {graph_path}")

def visualize_interactive(graph, output_file):
    # Ensure the directory exists
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # Create the directory if it doesn't exist

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

def build_graph_initiate(links,output_dir,output_graph_dir):
    # Build the graph
    graph = build_graph(output_dir, links)
    # remove all edges with type variable
    edges_to_remove = [(source, target) for source, target, data in graph.edges(data=True) if data.get("type") == "variable"]
    graph.remove_edges_from(edges_to_remove)
    

    # Save the graph to a file (optional)
    file_name = links[0] if links else "class_graph"
    html_path = os.path.join(output_graph_dir, f"{file_name}.html")
    visualize_interactive(graph, html_path)
    save_graph_to_gml(graph, output_graph_dir,f"{file_name}.gml")  # Save in GML format for visualization

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
    period = time.time()  # Start time for performance measurement
    prompt_token = 0
    response_token = 0
    
    # Step 5: Compute results for all nodes starting from leaf nodes
    node = next(iter(graph.nodes)) # Get one node from the reversed graph
    prompt_token, response_token = compute_result(node,node_results,graph,visited_nodes,processing_nodes)
    period = time.time() - period  # End time for performance measurement
    # Get the next node to process
       
    return node_results,period, prompt_token, response_token


# Step 4: Define a helper function for dynamic programming
def compute_result(node,node_results,graph,visited_nodes,processing_nodes,prompt_token=0,response_token=0):
   
    if node in processing_nodes:
        print(f"Node {node} has already been visited, using cached value.")
        return prompt_token, response_token  # Return the number of tokens in the response and prompt
    
    # Mark the node as being processed
    processing_nodes.add(node)

    # If the result for the current node is already computed, return it
    if graph.out_degree(node) == 0:
        print(f"Node {node} is a leaf node, returning its value.")
        node_attributes = graph.nodes[node]  # Access the node's attributes
        if node_attributes.get("comment") is not None and node_attributes.get("comment") != "" and node_attributes.get("comment") != "No comment available":
            # If the node has a comment, create a prompt and interact with DeepSeek
            prompt_instance = prompt.create_prompt_method(node, node_attributes.get("comment", ""))
            response = prompt.interact_with_deepseek(prompt_instance)
            node_results[node] = str(response)
            log_response(response, prompt_instance, node, prompt_token, response_token)
            return prompt_token+prompt.get_tokens_deepseek(prompt_instance), response_token+prompt.get_tokens_deepseek(response)  # Return the number of tokens in the response and prompt
            # add code for logging the response and the number of tokens and run-time infomrmation
        else :
            # If the node has no comment, return its name
            node_results[node] = ""
        visited_nodes.add(node)  # Mark the node as visited
        #processing_nodes.remove(node)
        return prompt_token, response_token  # Return the number of tokens in the response and prompt
    
    
    print(f"Computing result for node: {node}")
    successors = list(graph.successors(node)) 
    for successor in successors:  # Ensure `node` is a valid identifier
        if successor not in node_results and successor not in processing_nodes:            
            prompt_token,response_token = compute_result(successor, node_results, graph, visited_nodes, processing_nodes,prompt_token, response_token)

    response_init =""
    # Merge successor results and compute the current node's value
    if len(successors) == 0:
        print(f"No successors found for node {node}, skipping.")
    elif len(successors) == 1:
        # If there's only one successor, use its result directly
        successor = successors[0]
        node_attributes = graph.nodes[node] # Access the node's attributes
        response_init = node_results.get(successor, "")
        prompt_instance = prompt.create_prompt_class(node_attributes.get("name"), node_attributes.get("comment", ""),response_init)
        response_init = prompt.interact_with_deepseek(prompt_instance)
        if response_init is not None or response_init != "":
            response_token += prompt.get_tokens_deepseek(response_init)
        prompt_token += prompt.get_tokens_deepseek(prompt_instance)
        log_response(response_init, prompt_instance, node, prompt_token, response_token)
        node_results[node] = str(response_init)
    else:
        # get first successor of node
        response_init = node_results.get(successors[0], "")  # Use the first successor's result as the initial response
        for successor in successors[1:]:
            if successor not in node_results and successor not in visited_nodes:
                print(f"Successor {successor} not found in node_results, skipping.")
                continue
            prompt_instance = prompt.merge_prompts(graph.nodes[successor].get("name"),node_results[successor],response_init)
            response_init = prompt.interact_with_deepseek(prompt_instance)
            prompt_token += prompt.get_tokens_deepseek(prompt_instance)
            if response_init is not None or response_init != "":
                response_token += prompt.get_tokens_deepseek(response_init)
            
            if response_init is None or response_init == "":
                print(f"Response for node {node} is None or empty, skipping.")
                continue
        log_response(response_init, None, node, prompt_token, response_token)
        node_results[node] = str(response_init)  # Store the final result for the node
        #print(f"Final result for node {node}: {node_results[node]}")
    # node_results[node] = str(node) + " -> " + ", " response_init  # Store the result in the node_results dictionary
    visited_nodes.add(node)  # Mark the node as visited
    #processing_nodes.remove(node)  # Remove the node from processing set
    return prompt_token, response_token  # Return the number of tokens in the response and prompt

    
def log_response(response, prompt, node, prompt_token, response_token):
    """
    Log the response, prompt, node, period, prompt token count, and response token count.
    """
    log_entry = {
        "response": response,
        "node": node,
        "prompt_token": prompt_token,
        "response_token": response_token
    }
    with open("response_log.json", "a") as log_file:
        json.dump(log_entry, log_file)
        log_file.write("\n")  # Write a newline for each entry

def build_graph_from_json(output_dir, output_graph_dir, class_name):
    print(f"Building graph from JSON files in {output_dir} for classes: {class_name}")
    class_file = find_class_file(output_dir, class_name)
    print(f"Class file found: {class_file}.json")
    if class_file:
        print(f"Class file found for {class_name}: {class_file}")
        graph = build_graph_initiate([class_name], output_dir,output_graph_dir)
        return graph
    return None


def find_graph(class_name, output_dir):
    """
    Find the graph for a specific class in the output directory.
    """
    class_graph_name = f"{class_name}.gml" 
    class_graph_path = os.path.join(output_dir, class_graph_name)
    if os.path.exists(class_graph_path):
        print(f"Graph file found for class {class_name}: {class_graph_path}")
        return nx.read_gml(class_graph_path)  # Load the graph from the GML file
    else:
        print(f"Graph file not found for class {class_name}.")
        return None
    
def handle_operation(output_json_dir, output_excel_dir, output_graph_dir):
    """
    Handle the operation that the user perform.
    """
    # Tell user about the available operations
    print(f" Choose one operation to perform:")
    print(f" 1. Read from Excel file and build the graph for each class (if not exists), then interact with LLM to find dependencies.")
    print(f" 2. Specify the path of excel file consisting of the list of classes. ")
    print(f" 3. Enter a class name and find its dependencies.")
    print(f" 4. Exit")
    
    # Get user input for the operation
    operation = input("Enter the operation you want to perform (e.g., 'find', 'analyze', etc.): ")
    # Perform the operation based on user input
    if operation == "1":
        # Read the Excel file and build the graph for each class
        class_names = read_excel_file(output_excel_dir)
        for class_name in class_names:
            graph = build_graph_from_json(output_json_dir, output_graph_dir, class_names)
        print(f"Graph built with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")
        
    elif operation == "2":
        # Specify the path of the Excel file
        file_path = input("Enter the path of the Excel file: ")
        file_path = output_excel_dir + "/" + file_path if not file_path.startswith("/") else file_path
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist. Please check the path and try again.")
            return None
        class_names = read_excel_file(file_path)
        for class_name in class_names:
            graph = build_graph_from_json(output_json_dir, output_graph_dir,class_names)
        print(f"Graph built with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")
    elif operation == "3":
        # Enter a class name and find its dependencies
        class_name = input("Enter the class name to find its dependencies: ")
        class_graph = find_graph(class_name, output_graph_dir)
        if class_graph is None:
            # If the graph for the class is not found, check if json file exists, 
            graph = build_graph_from_json(output_json_dir, output_graph_dir,class_name)
            if graph is None:
                # If the graph is still not found, print an error message
                print(f"Graph for class {class_name} not found. Please ensure the class name is correct and the graph exists in the output directory.")
                return None
            
            print(f"Graph for class {class_name} built with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")
        else:
            traverse_from_leaves_to_roots_with_cycles(class_graph)
            print(f"Graph for class {class_name} found with {class_graph.number_of_nodes()} nodes and {class_graph.number_of_edges()} edges.")
        
    elif operation == "4":
        # Exit the program
        print("Exiting the program.")
        return None
    else:
        print(f"Invalid operation: {operation}. Please choose a valid operation.")
        return None
    
    # Example operation: just return the node name
    return str(operation)  # Convert the operation to a string representation

def main():
    # Paths
    output_json_dir = "/home/maryam/clearblue/java-code/java-code/output"
    output_excel_dir = "/home/maryam/clearblue/java-code/java-code/py-code/functions"
    output_graph_dir = "/home/maryam/clearblue/java-code/java-code/py-code/graphs"
    # Ensure the output directory exists
    if not os.path.exists(output_json_dir):
        os.makedirs(output_json_dir)
    if not os.path.exists(output_excel_dir):
        os.makedirs(output_excel_dir)

    handle_operation(output_json_dir, output_excel_dir, output_graph_dir)


if __name__ == "__main__":
    main()