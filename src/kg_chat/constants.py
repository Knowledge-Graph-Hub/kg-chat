"""Constants for the Knowledge Graph Chatbot."""

from functools import lru_cache
from pathlib import Path

from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI

PWD = Path(__file__).parent
DATA_DIR = PWD / "data"
GRAPH_OUTPUT_DIR = PWD / "graph_output"
# NODES_FILE = DATA_DIR / "nodes.tsv"
# EDGES_FILE = DATA_DIR / "edges.tsv"
NODES_FILE = DATA_DIR / "merged-kg_nodes.tsv"
EDGES_FILE = DATA_DIR / "merged-kg_edges.tsv"

# Set environment variables for Neo4j connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_BATCH_SIZE = 2000  # Adjust the batch size as needed
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"
MODEL = "gpt-4o"

neo4j_wrapper_chain = None


@lru_cache(1)
def _initialize_neo4j_wrapper_chain():
    global neo4j_wrapper_chain
    """Initialize Neo4j."""
    if neo4j_wrapper_chain is None:
        graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
        llm = ChatOpenAI(model=MODEL, temperature=0)
        neo4j_wrapper_chain = GraphCypherQAChain.from_llm(graph=graph, llm=llm, verbose=True)
    return neo4j_wrapper_chain
