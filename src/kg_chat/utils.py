"""Utility functions for the KG chatbot."""

import webbrowser

from pyvis.network import Network

from kg_chat.constants import GRAPH_OUTPUT_DIR


def extract_nodes_edges(structured_result):
    """Extract nodes and edges from the structured result."""
    nodes = structured_result.get("nodes", [])
    edges = structured_result.get("edges", [])

    return nodes, edges


def structure_query(query: str):
    """Structure the query to request structured results."""
    if "show me" in query.lower():
        # Modify the query to request structured results
        structured_query = f"""
        {query}
        Please provide the result in JSON format with ALL nodes and ALL edges. Return JSON ONLY.
        Example: {{
            "nodes": [
                {{"label": "A", "id": "1"}},
                {{"label": "B", "id": "2"}},
                {{"label": "C", "id": "3"}},
                ..and so on
            ],
            "edges": [
                {{"source": {{"label": "A", "id": "1"}},
                "target": {{"label": "B", "id": "2"}},
                "relationship": "biolink:related_to"}},
                ..and so on
            ]
        }}
        """
    else:
        structured_query = query
    return structured_query


def visualize_kg(nodes, edges, app: bool = False):
    """Visualize the knowledge graph using pyvis."""
    # Create a PyVis network
    net = Network(notebook=False, cdn_resources="in_line")

    if not nodes:
        print("No nodes to display.")
        return

    # Track added nodes to avoid duplicates
    added_nodes = set()

    # Add nodes to the network
    for node in nodes:
        net.add_node(node["id"], label=node["label"])
        added_nodes.add(node["id"])

    # Add edges to the network
    for edge in edges:
        source_id = edge["source"]["id"]
        target_id = edge["target"]["id"]

        # Ensure both source and target nodes are added
        if source_id not in added_nodes:
            net.add_node(source_id, label=edge["source"].get("label", ""))
            added_nodes.add(source_id)
        if target_id not in added_nodes:
            net.add_node(target_id, label=edge["target"].get("label", ""))
            added_nodes.add(target_id)

        # Add edge with title (relationship)
        net.add_edge(source_id, target_id, title=edge.get("relationship"))

    # Generate and display the network
    html_file = str(GRAPH_OUTPUT_DIR / "knowledge_graph.html")
    net.show(html_file, notebook=False)

    # Open the generated HTML file in the default web browser
    webbrowser.open(html_file)
    if app:
        # Generate the HTML representation
        return net.generate_html()
