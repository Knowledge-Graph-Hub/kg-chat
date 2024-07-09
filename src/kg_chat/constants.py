"""Constants for the Knowledge Graph Chatbot."""

from pathlib import Path

PWD = Path(__file__).parent
DATA_DIR = PWD / "data"
NODES_FILE = DATA_DIR / "nodes.tsv"
EDGES_FILE = DATA_DIR / "edges.tsv"
# NODES_FILE = DATA_DIR / "merged-kg_nodes.tsv"
# EDGES_FILE = DATA_DIR / "merged-kg_edges.tsv"

NEO4J_BATCH_SIZE = 2000  # Adjust the batch size as needed
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"
