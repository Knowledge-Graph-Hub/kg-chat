"""Implementation of the DatabaseInterface for Neo4j."""

import csv
import time
from pathlib import Path
from pprint import pprint
from typing import Union

from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_ollama import ChatOllama
from neo4j import GraphDatabase

from kg_chat.config.llm_config import LLMConfig
from kg_chat.constants import (
    DATALOAD_BATCH_SIZE,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USERNAME,
)
from kg_chat.interface.database_interface import DatabaseInterface
from kg_chat.utils import llm_factory, structure_query


class Neo4jImplementation(DatabaseInterface):
    """Implementation of the DatabaseInterface for Neo4j."""

    def __init__(
        self,
        data_dir: Union[str, Path],
        uri: str = NEO4J_URI,
        username: str = NEO4J_USERNAME,
        password: str = NEO4J_PASSWORD,
        llm_config: LLMConfig = None,
    ):
        """Initialize the Neo4j database and the Langchain components."""
        if not data_dir:
            raise ValueError("Data directory is required. This typically contains the KGX tsv files.")
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.graph = Neo4jGraph(url=uri, username=username, password=password)
        self.llm = llm_factory(llm_config)
        self.data_dir = Path(data_dir)

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
                {Node: [['id'], ['category'], ['label']]},
                {RELATIONSHIP: [['subject'], ['predicate'], ['object']]}
            )
            """
        )
        print("Indexes ensured using APOC.")

    def get_human_response(self, prompt: str):
        """Get a human response from the Neo4j database."""
        human_response = self.chain.invoke({"query": prompt})
        pprint(human_response["result"])
        return human_response["result"]

    def get_structured_response(self, prompt: str):
        """Get a structured response from the Neo4j database."""
        if isinstance(self.llm, ChatOllama):
            if "show me" in prompt.lower():
                self.llm.format = "json"
        response = self.chain.invoke({"query": structure_query(prompt)})
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
            MATCH (a:Node {id: edge.subject})
            MATCH (b:Node {id: edge.object})
            CREATE (a)-[r:RELATIONSHIP {type: edge.predicate}]->(b)
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
            CREATE (n:Node {id: node.id, category: node.category, label: node.label})
        """,
            nodes=nodes,
        )

    def show_schema(self):
        """Show the schema of the Neo4j database."""
        with self.driver.session() as session:
            result = session.read_transaction(lambda tx: list(tx.run("CALL db.schema.visualization()")))
            pprint(result)

    def load_kg(self, block_size: int = DATALOAD_BATCH_SIZE):
        """Load the Knowledge Graph into the Neo4j database."""
        nodes_filepath = self.data_dir / "nodes.tsv"
        edges_filepath = self.data_dir / "edges.tsv"

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
            columns_of_interest = ["id", "category", "name", "description"]

            with open(nodes_filepath, "r") as nodes_file:
                reader = csv.DictReader(nodes_file, delimiter="\t")
                node_batch_loaded = 0

                # Determine which label column to use
                label_column = "name" if "name" in reader.fieldnames else "description"

                for row in reader:
                    node_id = row[columns_of_interest[0]]
                    node_category = row[columns_of_interest[1]]
                    node_label = row[label_column]
                    nodes_batch.append({"id": node_id, "category": node_category, "label": node_label})
                    node_batch_loaded += 1

                    if len(nodes_batch) >= block_size:
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

            with open(edges_filepath, "r") as edges_file:
                reader = csv.DictReader(edges_file, delimiter="\t")
                edge_batch_loaded = 0

                for row in reader:
                    subject = row[edge_column_of_interest[0]]
                    predicate = row[edge_column_of_interest[1]]
                    object = row[edge_column_of_interest[2]]
                    edges_batch.append({"subject": subject, "predicate": predicate, "object": object})
                    edge_batch_loaded += 1

                    if len(edges_batch) >= block_size / 2:
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
