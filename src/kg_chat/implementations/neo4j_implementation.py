"""Implementation of the DatabaseInterface for Neo4j."""

import csv
from pprint import pprint

from kg_chat.constants import (
    DATALOAD_BATCH_SIZE,
    EDGES_FILE,
    MODEL,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USERNAME,
    NODES_FILE,
    OPENAI_KEY,
)
from kg_chat.interface.database_interface import DatabaseInterface
from kg_chat.utils import structure_query
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase


class Neo4jImplementation(DatabaseInterface):
    """Implementation of the DatabaseInterface for Neo4j."""

    def __init__(self):
        """Initialize the Neo4j database and the Langchain components."""
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        self.graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
        self.llm = ChatOpenAI(model=MODEL, temperature=0, api_key=OPENAI_KEY)
        self.chain = GraphCypherQAChain.from_llm(graph=self.graph, llm=self.llm, verbose=True)

    def execute_query(self, query: str):
        """Execute a Cypher query against the Neo4j database."""
        with self.driver.session() as session:
            result = session.read_transaction(lambda tx: list(tx.run(query)))
        return result

    def execute_query_using_langchain(self, query: str):
        """Execute a Cypher query against the Neo4j database using Langchain."""
        result = self.graph.query(query)
        return result

    def clear_database(self, tx):
        """Clear the Neo4j database."""
        tx.run("MATCH (n) DETACH DELETE n")

    def get_human_response(self, query: str):
        """Get a human response from the Neo4j database."""
        human_response = self.chain.invoke({"query": query})
        pprint(human_response["result"])
        return human_response["result"]

    def get_structured_response(self, query: str):
        """Get a structured response from the Neo4j database."""
        response = self.chain.invoke({"query": structure_query(query)})
        return response["result"]

    def create_edges(self, tx, edges):
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

    def create_nodes(self, tx, nodes):
        """Create nodes in the Neo4j database."""
        tx.run(
            """
            UNWIND $nodes AS node
            CREATE (n:Node {id: node.id, label: node.label})
        """,
            nodes=nodes,
        )

    def show_schema(self):
        """Show the schema of the Neo4j database."""
        with self.driver.session() as session:
            result = session.read_transaction(lambda tx: list(tx.run("CALL db.schema.visualization()")))
            pprint(result)

    def ensure_index(self, tx):
        """Ensure that the index on :Node(id) exists."""
        query = (
            "CALL db.indexes() YIELD name, state, type, entityType, labelsOrTypes, properties "
            "WHERE labelsOrTypes = ['Node'] AND properties = ['id'] RETURN name"
        )
        result = tx.run(query)
        if not result.single():
            print("Creating index on :Node(id)...")
            tx.run("CREATE INDEX ON :Node(id)")
            print("Index created.")
        else:
            print("Index on :Node(id) already exists.")

    def load_kg(self):
        """Load the Knowledge Graph into the Neo4j database."""
        with self.driver.session() as session:
            # Clear the existing database
            print("Clearing the existing database...")
            session.write_transaction(self.clear_database)
            print("Database cleared.")

            # Ensure indexes are created
            print("Ensuring indexes...")
            session.write_transaction(self.ensure_index)
            print("Indexes ensured.")

            # Import nodes in batches
            print("Starting to import nodes...")
            nodes_batch = []
            columns_of_interest = ["id", "name"]

            with open(NODES_FILE, "r") as nodes_file:
                reader = csv.DictReader(nodes_file, delimiter="\t")
                node_batch_loaded = 0

                for row in reader:
                    node_id = row[columns_of_interest[0]]
                    node_label = row[columns_of_interest[1]]
                    nodes_batch.append({"id": node_id, "label": node_label})
                    node_batch_loaded += 1

                    if len(nodes_batch) >= DATALOAD_BATCH_SIZE:
                        session.write_transaction(self.create_nodes, nodes_batch)
                        nodes_batch = []
                        # print(f"Batch loaded (nodes): {node_batch_loaded} nodes")

                if nodes_batch:
                    session.write_transaction(self.create_nodes, nodes_batch)

            print(f"Nodes import completed {node_batch_loaded}.")

            # Import edges in batches
            print("Starting to import edges...")
            edges_batch = []
            edge_column_of_interest = ["subject", "predicate", "object"]

            with open(EDGES_FILE, "r") as edges_file:
                reader = csv.DictReader(edges_file, delimiter="\t")
                edge_batch_loaded = 0

                for row in reader:
                    source_id = row[edge_column_of_interest[0]]
                    relationship = row[edge_column_of_interest[1]]
                    target_id = row[edge_column_of_interest[2]]
                    edges_batch.append({"source_id": source_id, "target_id": target_id, "relationship": relationship})
                    edge_batch_loaded += 1

                    if len(edges_batch) >= DATALOAD_BATCH_SIZE / 5:
                        session.write_transaction(self.create_edges, edges_batch)
                        edges_batch = []
                        # print(f"Batch loaded (edges): {edge_batch_loaded}")

                if edges_batch:
                    session.write_transaction(self.create_edges, edges_batch)
                    print(f"Batch written (edges): {edge_batch_loaded}")

            print(f"Edges import completed: {edge_batch_loaded} edges.")

        self.driver.close()
        print("Import process finished and connection closed.")
