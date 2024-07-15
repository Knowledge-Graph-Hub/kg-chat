"""Implementation of the DatabaseInterface for Neo4j."""

import csv
from pprint import pprint
import time

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

    def __init__(self, read_only=True):
        """Initialize the Neo4j database and the Langchain components."""
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        self.graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
        self.llm = ChatOpenAI(model=MODEL, temperature=0, api_key=OPENAI_KEY)
        self.chain = GraphCypherQAChain.from_llm(graph=self.graph, llm=self.llm, verbose=True)
        self.read_only = read_only

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
        if self.read_only:
            raise PermissionError("Write operations are not allowed in read-only mode.")
        
        with self.driver.session() as session:
            session.write_transaction(self._clear_database)

    @staticmethod
    def _clear_database(tx):
        """Helper method to clear the Neo4j database using APOC."""
        tx.run("""
        CALL apoc.periodic.iterate(
            'MATCH (n) RETURN n',
            'DETACH DELETE n',
            {batchSize:1000, parallel:true}
        )
        """)

    def ensure_index(self, tx):
        """Ensure that the index on :Node(id) exists."""
        if self.read_only:
            raise PermissionError("Write operations are not allowed in read-only mode.")
        
        # Use APOC to ensure the index exists
        tx.run("""
        CALL apoc.schema.assert(
            {Node: [['id']]},
            {RELATIONSHIP: [['source_id'], ['target_id']]}
        )
        """)
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

    def create_edges(self, tx, edges):
        """Create relationships between nodes."""
        if self.read_only:
            raise PermissionError("Write operations are not allowed in read-only mode.")
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
        if self.read_only:
            raise PermissionError("Write operations are not allowed in read-only mode.")
        tx.run(
            """
            UNWIND $nodes AS node
            CREATE (n:Node {id: node.id, label: node.label})
        """,
            nodes=nodes,
        )
    # def create_nodes(self, tx, file_path):
    #     query = """
    #     CALL apoc.periodic.iterate($load_query,
    #     "CREATE (:Node {node_id: row.id, node_label: row.name})",
    #     {batchSize:10000, iterateList:true, parallel:true}
    #     )
    #     """
    #     load_query = f"CALL apoc.load.csv('{file_path}', {{sep: '\t'}}) YIELD map AS row RETURN row"
    #     return tx.run(query, load_query=load_query)

    # def create_edges(self, tx, file_path):
    #     query = """
    #     CALL apoc.periodic.iterate($load_query,
    #     "MATCH (source:Node {node_id: row.subject})
    #     MATCH (target:Node {node_id: row.object})
    #     CREATE (source)-[r:RELATIONSHIP {type: row.predicate}]->(target)",
    #     {batchSize:10000, iterateList:true, parallel:true}
    #     )
    #     """
    #     load_query = f"CALL apoc.load.csv('{file_path}', {{sep: '\t'}}) YIELD map AS row RETURN row"
    #     return tx.run(query, load_query=load_query)

    def show_schema(self):
        """Show the schema of the Neo4j database."""
        with self.driver.session() as session:
            result = session.read_transaction(lambda tx: list(tx.run("CALL db.schema.visualization()")))
            pprint(result)

    def load_kg(self):
        """Load the Knowledge Graph into the Neo4j database."""
        if self.read_only:
            raise PermissionError("Write operations are not allowed in read-only mode.")
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
                        session.write_transaction(self.create_nodes, nodes_batch)
                        nodes_batch = []
                        # print(f"Batch loaded (nodes): {node_batch_loaded} nodes")

                if nodes_batch:
                    session.write_transaction(self.create_nodes, nodes_batch)
            
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
                        session.write_transaction(self.create_edges, edges_batch)
                        edges_batch = []
                        # print(f"Batch loaded (edges): {edge_batch_loaded}")

                if edges_batch:
                    session.write_transaction(self.create_edges, edges_batch)

            elapsed_time_seconds = time.time() - start_time
            if elapsed_time_seconds >= 3600:
                elapsed_time_hours = elapsed_time_seconds / 3600
                print(f"Edges import completed: {edge_batch_loaded} edges in {elapsed_time_hours:.2f} hours.")
            else:
                elapsed_time_minutes = elapsed_time_seconds / 60
                print(f"Edges import completed: {edge_batch_loaded} edges in {elapsed_time_minutes:.2f} minutes.")

        self.driver.close()
        print("Import process finished and connection closed.")
