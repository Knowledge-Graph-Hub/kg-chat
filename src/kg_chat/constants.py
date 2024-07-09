from pathlib import Path


PWD = Path(__file__).parent
DATA_DIR = PWD / "data"
NODES_FILE = DATA_DIR / "nodes.tsv"
EDGES_FILE = DATA_DIR / "edges.tsv"

NEO4J_BATCH_SIZE = 2000  # Adjust the batch size as needed