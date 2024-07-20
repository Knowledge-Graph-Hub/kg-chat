"""Constants for the Knowledge Graph Chatbot."""

from os import getenv
from pathlib import Path

PWD = Path(__file__).resolve().parent
PROJ_DIR = PWD.parents[1]
DATA_DIR = PROJ_DIR / "data"
GRAPH_OUTPUT_DIR = PWD / "graph_output"
ASSETS_DIR = PWD / "assets"

OPENAI_KEY = getenv("OPENAI_API_KEY")
OPEN_AI_MODEL = "gpt-4o"

DATALOAD_BATCH_SIZE = 5000  # Adjust the batch size as needed

# Set environment variables for Neo4j connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"


DATABASE_DIR = PWD / "database"
