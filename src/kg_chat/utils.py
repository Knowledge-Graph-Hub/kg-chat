"""Utility functions for the KG chatbot."""

import random
import webbrowser

from pyvis.network import Network

from kg_chat.constants import GRAPH_OUTPUT_DIR

PREFIX_COLOR_MAP = {}


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
                {{"label": "A", "id": "1", category: "biolink:Gene"}},
                {{"label": "B", "id": "2", category: "biolink:ChemicalSubstance"}},
                {{"label": "C", "id": "3", category: "biolink:Disease"}},
                ..and so on
            ],
            "edges": [
                {{"subject": {{"label": "A", "id": "1"}},
                "object": {{"label": "B", "id": "2"}},
                "predicate": "biolink:related_to"}},
                ..and so on
            ]
        }}
        """
    else:
        structured_query = query
    return structured_query


def generate_random_color():
    """Generate a random color."""
    while True:
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        if color not in PREFIX_COLOR_MAP.values():
            return color


def assign_color_to_prefix(curie):
    """Assign a color to a prefix."""
    prefix = curie.split(":")[0]
    if prefix not in PREFIX_COLOR_MAP:
        PREFIX_COLOR_MAP[prefix] = generate_random_color()
    print(f"PREFIX_COLOR_MAP={PREFIX_COLOR_MAP}")
    return PREFIX_COLOR_MAP[prefix]


def visualize_kg(nodes, edges, app: bool = False):
    """Visualize the knowledge graph using pyvis."""
    # Create a PyVis network
    net = Network(
        notebook=False,
        cdn_resources="in_line",
        neighborhood_highlight=True,
        select_menu=True,
        filter_menu=True,
    )

    if not nodes:
        print("No nodes to display.")
        return

    # Track added nodes to avoid duplicates
    added_nodes = set()

    # Add nodes to the network
    for node in nodes:
        # based on prefix (node["id"].split(":")[0]) assign nodes to color

        net.add_node(
            node["id"],
            label=node["label"],
            category=node.get("category", ""),
            title=node.get("id", ""),
            color=assign_color_to_prefix(node["id"]),
        )
        added_nodes.add(node["id"])

    # Add edges to the network
    for edge in edges:
        subject = edge["subject"]["id"]
        object = edge["object"]["id"]

        # Ensure both subject and object nodes are added
        if subject not in added_nodes:
            net.add_node(
                subject,
                label=edge["subject"].get("label", ""),
                category=edge["subject"].get("category", ""),
                title=subject,
                color=assign_color_to_prefix(subject),
            )
            added_nodes.add(subject)
        if object not in added_nodes:
            net.add_node(
                object,
                label=edge["object"].get("label", ""),
                category=edge["object"].get("category", ""),
                title=object,
                color=assign_color_to_prefix(object),
            )
            added_nodes.add(object)

        # Add edge with title (predicate)
        net.add_edge(subject, object, title=edge.get("predicate"))

    # Generate and display the network
    html_file = str(GRAPH_OUTPUT_DIR / "knowledge_graph.html")
    net.show(html_file, notebook=False)

    # Open the generated HTML file in the default web browser
    webbrowser.open(html_file)
    if app:
        # Generate the HTML representation
        return net.generate_html()
