"""DuckDBImplementation class that implements the DatabaseInterface for DuckDB."""

import tempfile
from pprint import pprint

import duckdb
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine

from kg_chat.constants import (
    DATABASE_DIR,
    EDGES_FILE,
    MODEL,
    NODES_FILE,
    OPENAI_KEY,
)
from kg_chat.interface.database_interface import DatabaseInterface
from kg_chat.utils import structure_query


class DuckDBImplementation(DatabaseInterface):
    """Implementation of the DatabaseInterface for DuckDB."""

    def __init__(self, read_only=True):
        """Initialize the DuckDB database and the Langchain components."""
        self.conn = duckdb.connect(database=str(DATABASE_DIR / "kg_chat.db"))
        # self.read_only_conn = duckdb.connect(database=str(DATABASE_DIR / "kg_chat.db"), read_only=True)
        self.llm = ChatOpenAI(model=MODEL, temperature=0, api_key=OPENAI_KEY)
        # Langchain relevant portion
        self.engine = create_engine("duckdb:///src/kg_chat/database/kg_chat.db")
        self.db = SQLDatabase(self.engine, view_support=True)
        self.agent = create_sql_agent(llm=self.llm, db=self.db, agent_type="openai-tools", verbose=True)
        self.read_only = read_only

    def execute_query(self, query: str):
        """Execute a query against the DuckDB database."""
        if self.read_only:
            result = self.conn.execute(query).fetchall()
        else:
            result = self.conn.execute(query).fetchall()
            self.conn.close()
        return result

    def clear_database(self):
        """Clear the DuckDB database."""
        if self.read_only:
            raise PermissionError("Write operations are not allowed in read-only mode.")
        self.conn.execute("DROP TABLE IF EXISTS edges")
        self.conn.execute("DROP TABLE IF EXISTS nodes")
        self.conn.close()

    def get_human_response(self, prompt: str):
        """Get a human response from the DuckDB database."""
        response = self.agent.invoke(prompt)
        # pprint(response["output"])
        return response["output"]

    def get_structured_response(self, prompt: str):
        """Get a structured response from the DuckDB database."""
        prompt_for_structured_query = structure_query(prompt)
        response = self.agent.invoke(prompt_for_structured_query)
        return response["output"]

    def create_edges(self, edges):
        """Create relationships between nodes."""
        if self.read_only:
            raise PermissionError("Write operations are not allowed in read-only mode.")
        self.conn.executemany(
            """
            INSERT INTO edges (source_id, target_id, relationship) VALUES (?, ?, ?)
            """,
            edges,
        )

    def create_nodes(self, nodes):
        """Create nodes in the DuckDB database."""
        if self.read_only:
            raise PermissionError("Write operations are not allowed in read-only mode.")
        self.conn.executemany(
            """
            INSERT INTO nodes (id, label) VALUES (?, ?)
            """,
            nodes,
        )

    def show_schema(self):
        """Show the schema of the DuckDB database."""
        result = self.conn.execute("PRAGMA show_tables").fetchall()
        pprint(result)

    def execute_query_using_langchain(self, prompt: str):
        """Execute a query against the DuckDB database using Langchain."""
        result = self.agent.invoke(prompt)
        return result["output"]

    def load_kg(self):
        """Load the Knowledge Graph into the DuckDB database."""
        # Clear the existing database
        print("Clearing the existing database...")
        self.clear_database()
        print("Database cleared.")

        # Create tables
        self.conn.execute(
            """
            CREATE TABLE nodes (
                id VARCHAR PRIMARY KEY,
                label VARCHAR
            )
        """
        )
        self.conn.execute(
            """
            CREATE TABLE edges (
                source_id VARCHAR,
                relationship VARCHAR,
                target_id VARCHAR,
            )
        """
            # removed the constrains for now
            # FOREIGN KEY(source_id) REFERENCES nodes(id),
            # FOREIGN KEY(target_id) REFERENCES nodes(id)
        )

        # Import nodes in batches using DuckDB's COPY command for efficiency
        print("Starting to import nodes...")
        columns_of_interest = ["id", "name"]
        with open(NODES_FILE, "r") as nodes_file:
            header_line = nodes_file.readline().strip().split("\t")
            column_indexes = {col: idx for idx, col in enumerate(header_line) if col in columns_of_interest}

            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_nodes_file:
                temp_nodes_file.write("\t".join(columns_of_interest) + "\n")
                for line in nodes_file:
                    columns = line.strip().split("\t")
                    if len(columns) > max(column_indexes.values()):
                        node_id = columns[column_indexes["id"]]
                        node_label = columns[column_indexes["name"]]
                        temp_nodes_file.write(f"{node_id}\t{node_label}\n")
                temp_nodes_file.flush()

                # Load data from temporary file into DuckDB
                self.conn.execute(f"COPY nodes FROM '{temp_nodes_file.name}' (DELIMITER '\t', HEADER)")
        print("Nodes import completed.")

        # Import edges in batches using DuckDB's COPY command for efficiency
        print("Starting to import edges...")
        edge_column_of_interest = ["subject", "predicate", "object"]
        with open(EDGES_FILE, "r") as edges_file:
            header_line = edges_file.readline().strip().split("\t")
            column_indexes = {col: idx for idx, col in enumerate(header_line) if col in edge_column_of_interest}

            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_edges_file:
                temp_edges_file.write("\t".join(edge_column_of_interest) + "\n")
                for line in edges_file:
                    columns = line.strip().split("\t")
                    source_id = columns[column_indexes["subject"]]
                    relationship = columns[column_indexes["predicate"]]
                    target_id = columns[column_indexes["object"]]
                    temp_edges_file.write(f"{source_id}\t{relationship}\t{target_id}\n")
                temp_edges_file.flush()

                # Load data from temporary file into DuckDB
                self.conn.execute(f"COPY edges FROM '{temp_edges_file.name}' (DELIMITER '\t', HEADER)")
        print("Edges import completed.")

        # Create indexes for faster querying
        print("Creating indexes...")
        self.conn.execute("CREATE INDEX idx_nodes_id ON nodes(id);")
        self.conn.execute("CREATE INDEX idx_edges_source_id ON edges(source_id);")
        self.conn.execute("CREATE INDEX idx_edges_target_id ON edges(target_id);")
        print("Indexes created.")
        self.conn.close()

        print("Import process finished.")
