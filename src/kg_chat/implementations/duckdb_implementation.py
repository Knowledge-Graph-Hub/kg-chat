"""Implementation of the DatabaseInterface for DuckDB."""

import tempfile
from pprint import pprint

import duckdb
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine

from kg_chat.constants import (
    DATABASE_DIR,
    EDGES_FILE,
    NODES_FILE,
    OPEN_AI_MODEL,
    OPENAI_KEY,
)
from kg_chat.interface.database_interface import DatabaseInterface
from kg_chat.utils import structure_query


class DuckDBImplementation(DatabaseInterface):
    """Implementation of the DatabaseInterface for DuckDB."""

    def __init__(self):
        """Initialize the DuckDB database and the Langchain components."""
        self.safe_mode = True
        self.conn = duckdb.connect(database=str(DATABASE_DIR / "kg_chat.db"))
        self.llm = ChatOpenAI(model=OPEN_AI_MODEL, temperature=0, api_key=OPENAI_KEY)
        self.engine = create_engine("duckdb:///src/kg_chat/database/kg_chat.db")
        self.db = SQLDatabase(self.engine, view_support=True)
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.agent = create_sql_agent(llm=self.llm, agent_type="openai-tools", verbose=True, toolkit=self.toolkit)

    def toggle_safe_mode(self, enabled: bool):
        """Toggle safe mode on or off."""
        self.safe_mode = enabled

    def is_safe_command(self, command: str) -> bool:
        """Check if a command is safe to execute."""
        unsafe_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "UPDATE", "INSERT"]
        return not any(keyword in command.upper() for keyword in unsafe_keywords)

    def execute_unsafe_operation(self, operation: callable):
        """Execute an unsafe operation."""
        original_safe_mode = self.safe_mode
        self.safe_mode = False
        try:
            result = operation()
        finally:
            self.safe_mode = original_safe_mode
        return result

    def execute_query(self, query: str):
        """Execute a SQL query against the DuckDB database."""
        if self.safe_mode and not self.is_safe_command(query):
            raise ValueError(f"Unsafe command detected: {query}")
        return self.conn.execute(query).fetchall()

    def clear_database(self):
        """Clear the database."""

        def _clear():
            self.conn.execute("DROP TABLE IF EXISTS edges")
            self.conn.execute("DROP TABLE IF EXISTS nodes")

        return self.execute_unsafe_operation(_clear)

    def get_human_response(self, prompt: str):
        """Get a human response from the database."""
        response = self.agent.invoke(prompt)
        return response["output"]

    def get_structured_response(self, prompt: str):
        """Get a structured response from the database."""
        prompt_for_structured_query = structure_query(prompt)
        response = self.agent.invoke(prompt_for_structured_query)
        return response["output"]

    def create_edges(self, edges):
        """Create edges in the database."""

        def _create_edges():
            self.conn.executemany(
                "INSERT INTO edges (source_id, target_id, relationship) VALUES (?, ?, ?)",
                edges,
            )

        return self.execute_unsafe_operation(_create_edges)

    def create_nodes(self, nodes):
        """Create nodes in the database."""

        def _create_nodes():
            self.conn.executemany(
                "INSERT INTO nodes (id, label) VALUES (?, ?)",
                nodes,
            )

        return self.execute_unsafe_operation(_create_nodes)

    def show_schema(self):
        """Show the schema of the database."""
        result = self.conn.execute("PRAGMA show_tables").fetchall()
        return pprint(result)

    def execute_query_using_langchain(self, prompt: str):
        """Execute a query against the database using Langchain."""
        result = self.agent.invoke(prompt)
        return result["output"]

    def load_kg(self):
        """Load the Knowledge Graph into the database."""

        def _load_kg():
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
                    target_id VARCHAR
                )
            """
            )

            # Import nodes
            print("Starting to import nodes...")
            self._import_nodes()
            print("Nodes import completed.")

            # Import edges
            print("Starting to import edges...")
            self._import_edges()
            print("Edges import completed.")

            # Create indexes for faster querying
            print("Creating indexes...")
            self.conn.execute("CREATE INDEX idx_nodes_id ON nodes(id);")
            self.conn.execute("CREATE INDEX idx_edges_source_id ON edges(source_id);")
            self.conn.execute("CREATE INDEX idx_edges_target_id ON edges(target_id);")
            print("Indexes created.")

            print("Import process finished.")

        return self.execute_unsafe_operation(_load_kg)

    def _import_nodes(self):
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

    def _import_edges(self):
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
