"""Utility functions for the KG chatbot."""

import webbrowser

from neo4j import GraphDatabase
from pyvis.network import Network

from kg_chat.constants import EDGES_FILE, GRAPH_OUTPUT_DIR, NEO4J_BATCH_SIZE, NODES_FILE


def clear_database(tx):
    """Clear the Neo4j database."""
    tx.run("MATCH (n) DETACH DELETE n")


def create_nodes(tx, nodes):
    """Create nodes in the Neo4j database."""
    tx.run(
        """
        UNWIND $nodes AS node
        CREATE (n:Node {id: node.id, label: node.label})
    """,
        nodes=nodes,
    )


def create_edges(tx, edges):
    """Create relationships between nodes."""
    tx.run(
        """
        UNWIND $edges AS edge
        MATCH (a:Node {id: edge.source_id})
        MATCH (b:Node {id: edge.target_id})
        CREATE (a)-[r:RELATIONSHIP {type: edge.relationship}]->(b)
    """,
        edges=edges,
    )


def get_column_indexes(header_line, columns_of_interest):
    """Get the indexes of the columns of interest."""
    headers = header_line.strip().split("\t")
    return {col: headers.index(col) for col in columns_of_interest}


def import_kg_into_neo4j():
    """Import KG into Neo4j using batching for better performance."""
    # Connect to Neo4j
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

    with driver.session() as session:
        # Clear the existing database
        print("Clearing the existing database...")
        session.write_transaction(clear_database)
        print("Database cleared.")

        # Import nodes in batches
        print("Starting to import nodes...")
        nodes_batch = []
        columns_of_interest = ["id", "name"]
        with open(NODES_FILE, "r") as nodes_file:
            header_line = nodes_file.readline()
            column_indexes = get_column_indexes(header_line, columns_of_interest)
            for line in nodes_file:
                columns = line.strip().split("\t")
                if len(columns) > column_indexes["name"] + 1:
                    node_id = columns[column_indexes["id"]]
                    node_label = columns[column_indexes["name"]]
                    nodes_batch.append({"id": node_id, "label": node_label})
                if len(nodes_batch) >= NEO4J_BATCH_SIZE:
                    session.write_transaction(create_nodes, nodes_batch)
                    nodes_batch = []
            if nodes_batch:
                session.write_transaction(create_nodes, nodes_batch)
        print("Nodes import completed.")

        # Import edges in batches
        print("Starting to import edges...")
        edges_batch = []
        edge_column_of_interest = ["subject", "predicate", "object"]
        with open(EDGES_FILE, "r") as edges_file:
            header_line = edges_file.readline()
            column_indexes = get_column_indexes(header_line, edge_column_of_interest)
            for line in edges_file:
                columns = line.strip().split("\t")
                source_id = columns[column_indexes["subject"]]
                relationship = columns[column_indexes["predicate"]]
                target_id = columns[column_indexes["object"]]
                edges_batch.append({"source_id": source_id, "target_id": target_id, "relationship": relationship})

                if len(edges_batch) >= NEO4J_BATCH_SIZE * 5:
                    session.write_transaction(create_edges, edges_batch)
                    edges_batch = []

            if edges_batch:
                session.write_transaction(create_edges, edges_batch)

        print("Edges import completed.")

    driver.close()
    print("Import process finished and connection closed.")


def extract_nodes_edges(structured_result):
    """Extract nodes and edges from the structured result."""
    nodes = structured_result.get("nodes", [])
    edges = structured_result.get("edges", [])

    return nodes, edges


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


def structure_query(query: str):
    """Structure the query to request structured results."""
    if "show me" in query.lower():
        # Modify the query to request structured results
        structured_query = f"""
        {query}
        Please provide the result in JSON format with nodes and edges.
        Example: {{
            "nodes": [
                {{"label": "A", "id": "1"}},
                {{"label": "B", "id": "2"}},
                {{"label": "C", "id": "3"}}
            ],
            "edges": [
                {{"source": {{"label": "A", "id": "1"}},
                "target": {{"label": "B", "id": "2"}},
                "relationship": "biolink:related_to"}}
            ]
        }}
        """
    else:
        structured_query = query
    return structured_query
