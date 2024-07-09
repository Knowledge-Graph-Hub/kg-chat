"""Utility functions for the KG chatbot."""

from neo4j import GraphDatabase

from kg_chat.constants import EDGES_FILE, NEO4J_BATCH_SIZE, NODES_FILE


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
                if len(columns) > column_indexes["name"]+1:
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


# Call the function to import the data
# import_kg_into_neo4j()
