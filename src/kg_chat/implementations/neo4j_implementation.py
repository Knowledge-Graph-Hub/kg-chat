"""Implementation of the DatabaseInterface for Neo4j."""

import csv
import time
from pprint import pprint

from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase

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


class Neo4jImplementation(DatabaseInterface):
    """Implementation of the DatabaseInterface for Neo4j."""

    def __init__(self):
        """Initialize the Neo4j database and the Langchain components."""
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        self.graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
        self.llm = ChatOpenAI(model=MODEL, temperature=0, api_key=OPENAI_KEY)

        self.chain = GraphCypherQAChain.from_llm(
            graph=self.graph,
            llm=self.llm,
            verbose=True,
            use_function_response=True,
            # function_response_system="Respond as a Data Scientist!",
            validate_cypher=True,
        )
        self.safe_mode = True

    def toggle_safe_mode(self, enabled: bool):
        """Toggle safe mode on or off."""
        self.safe_mode = enabled

    def is_safe_command(self, command: str) -> bool:
        """Check if a command is safe to execute."""
        unsafe_keywords = ["CREATE", "DELETE", "REMOVE", "SET", "MERGE", "DROP"]
        return not any(keyword in command.upper() for keyword in unsafe_keywords)

    def execute_unsafe_operation(self, operation: callable, *args, **kwargs):
        """Execute an unsafe operation."""
        original_safe_mode = self.safe_mode
        self.safe_mode = False
        try:
            result = operation(*args, **kwargs)
        finally:
            self.safe_mode = original_safe_mode
        return result

    def execute_query(self, query: str):
        """Execute a Cypher query against the Neo4j database."""
        if self.safe_mode and not self.is_safe_command(query):
            raise ValueError(f"Unsafe command detected: {query}")
        with self.driver.session() as session:
            result = session.read_transaction(lambda tx: list(tx.run(query)))
        return result

    def execute_query_using_langchain(self, query: str):
        """Execute a Cypher query against the Neo4j database using Langchain."""
        if self.safe_mode and not self.is_safe_command(query):
            raise ValueError(f"Unsafe command detected: {query}")
        result = self.graph.query(query)
        return result

    def clear_database(self):
        """Clear the Neo4j database."""

        def _clear_database():
            with self.driver.session() as session:
                session.write_transaction(self._clear_database_tx)

        return self.execute_unsafe_operation(_clear_database)

    @staticmethod
    def _clear_database_tx(tx):
        """Clear the Neo4j database using APOC."""
        tx.run(
            """
        CALL apoc.periodic.iterate(
            'MATCH (n) RETURN n',
            'DETACH DELETE n',
            {batchSize:1000, parallel:true}
        )
        """
        )

    def ensure_index(self):
        """Ensure that the index on :Node(id) exists."""

        def _ensure_index():
            with self.driver.session() as session:
                session.write_transaction(self._ensure_index_tx)

        return self.execute_unsafe_operation(_ensure_index)

    @staticmethod
    def _ensure_index_tx(tx):
        """Index existence check."""
        tx.run(
            """
        CALL apoc.schema.assert(
            {Node: [['id']]},
            {RELATIONSHIP: [['source_id'], ['target_id']]}
        )
        """
        )
        print("Indexes ensured using APOC.")

    def get_human_response(self, query: str):
        """Get a human response from the Neo4j database."""
        human_response = self.chain.invoke({"query": query})
        pprint(human_response["result"])
        return human_response["result"]

    def get_structured_response(self, query: str):
        """Get a structured response from the Neo4j database."""
        response = self.chain.invoke({"query": structure_query(query)})
        return response["result"]

    def create_edges(self, edges):
        """Create relationships between nodes."""

        def _create_edges():
            with self.driver.session() as session:
                session.write_transaction(self._create_edges_tx, edges)

        return self.execute_unsafe_operation(_create_edges)

    @staticmethod
    def _create_edges_tx(tx, edges):
        tx.run(
            """
            UNWIND $edges AS edge
            MATCH (a:Node {id: edge.source_id})
            MATCH (b:Node {id: edge.target_id})
            CREATE (a)-[r:RELATIONSHIP {type: edge.relationship}]->(b)
        """,
            edges=edges,
        )

    def create_nodes(self, nodes):
        """Create nodes in the Neo4j database."""

        def _create_nodes():
            with self.driver.session() as session:
                session.write_transaction(self._create_nodes_tx, nodes)

        return self.execute_unsafe_operation(_create_nodes)

    @staticmethod
    def _create_nodes_tx(tx, nodes):
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

    def load_kg(self):
        """Load the Knowledge Graph into the Neo4j database."""

        def _load_kg():
            # Clear the existing database
            print("Clearing the existing database...")
            self.clear_database()
            print("Database cleared.")

            # Ensure indexes are created
            print("Ensuring indexes...")
            self.ensure_index()
            print("Indexes ensured.")

            # Import nodes in batches
            print("Starting to import nodes...")
            start_time = time.time()
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
                        self.create_nodes(nodes_batch)
                        nodes_batch = []

                if nodes_batch:
                    self.create_nodes(nodes_batch)

            elapsed_time_seconds = time.time() - start_time

            if elapsed_time_seconds >= 3600:
                elapsed_time_hours = elapsed_time_seconds / 3600
                print(f"Nodes import completed: {node_batch_loaded} nodes in {elapsed_time_hours:.2f} hours.")
            else:
                elapsed_time_minutes = elapsed_time_seconds / 60
                print(f"Nodes import completed: {node_batch_loaded} nodes in {elapsed_time_minutes:.2f} minutes.")

            # Import edges in batches
            print("Starting to import edges...")
            start_time = time.time()
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

                    if len(edges_batch) >= DATALOAD_BATCH_SIZE / 2:
                        self.create_edges(edges_batch)
                        edges_batch = []

                if edges_batch:
                    self.create_edges(edges_batch)

            elapsed_time_seconds = time.time() - start_time
            if elapsed_time_seconds >= 3600:
                elapsed_time_hours = elapsed_time_seconds / 3600
                print(f"Edges import completed: {edge_batch_loaded} edges in {elapsed_time_hours:.2f} hours.")
            else:
                elapsed_time_minutes = elapsed_time_seconds / 60
                print(f"Edges import completed: {edge_batch_loaded} edges in {elapsed_time_minutes:.2f} minutes.")

            print("Import process finished.")

        return self.execute_unsafe_operation(_load_kg)

    def __del__(self):
        """Ensure the driver is closed when the object is destroyed."""
        if hasattr(self, "driver"):
            self.driver.close()
