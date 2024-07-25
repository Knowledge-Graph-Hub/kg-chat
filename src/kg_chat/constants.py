"""Constants for the Knowledge Graph Chatbot."""

from os import getenv
from pathlib import Path

PWD = Path(__file__).parent.resolve()
PROJ_DIR = PWD.parents[1]
ASSETS_DIR = PWD / "assets"
TEST_DIR = PROJ_DIR / "tests"
TESTS_INPUT_DIR = TEST_DIR / "input"
TESTS_OUTPUT_DIR = TEST_DIR / "output"

OPENAI_KEY = getenv("OPENAI_API_KEY")
OPEN_AI_MODEL = "gpt-4o"

OLLAMA_MODEL = "llama3.1" #!  not all models support tools (tool calling)

DATALOAD_BATCH_SIZE = 5000  # Adjust the batch size as needed

# Set environment variables for Neo4j connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"
