"""Implementation of the DatabaseInterface for DuckDB."""

import tempfile
import time
from pathlib import Path
from pprint import pprint
from typing import Union

import duckdb
from langchain.agents.agent import AgentExecutor, AgentType
from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_ollama import ChatOllama
from sqlalchemy import Engine, create_engine

from kg_chat.config.llm_config import LLMConfig
from kg_chat.interface.database_interface import DatabaseInterface
from kg_chat.utils import get_agent_prompt_template, llm_factory, structure_query


class DuckDBImplementation(DatabaseInterface):
    """Implementation of the DatabaseInterface for DuckDB."""

    def __init__(self, data_dir: Union[Path, str], llm_config: LLMConfig):
        """Initialize the DuckDB database and the Langchain components."""
        if not data_dir:
            raise ValueError("Data directory is required. This typically contains the KGX tsv files.")
        self.safe_mode = True
        self.data_dir = Path(data_dir)
        self.database_path = self.data_dir / "database/kg_chat.db"
        if not self.database_path.exists():
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: duckdb.DuckDBPyConnection = duckdb.connect(database=str(self.database_path))
        self.llm = llm_factory(llm_config)
        agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION
        self.engine: Engine = create_engine(f"duckdb:///{self.database_path}")
        self.db = SQLDatabase(self.engine, view_support=True)
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.agent: AgentExecutor = create_sql_agent(
            llm=self.llm,
            verbose=True,
            toolkit=self.toolkit,
            agent_type=agent_type,
            agent_executor_kwargs=dict(
                return_intermediate_steps=True,
                handle_parsing_errors=True,
            ),
            extra_tools=self.toolkit.get_tools(),
        )

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
        if isinstance(self.llm, ChatOllama):
            if "show me" in prompt.lower():
                self.llm.format = "json"

            structured_query = get_agent_prompt_template().format(
                input=prompt,
                tools=self.toolkit.get_tools(),
                tool_names=[tool.name for tool in self.toolkit.get_tools()],
                agent_scratchpad=None,
            )
        else:
            structured_query = {"input": structure_query(prompt)}

        response = self.agent.invoke(structured_query)
        return response["output"]

    def create_edges(self, edges):
        """Create edges in the database."""

        def _create_edges():
            self.conn.executemany(
                "INSERT INTO edges (subject, predicate, object) VALUES (?, ?, ?)",
                edges,
            )

        return self.execute_unsafe_operation(_create_edges)

    def create_nodes(self, nodes):
        """Create nodes in the database."""

        def _create_nodes():
            self.conn.executemany(
                "INSERT INTO nodes (id, category, label) VALUES (?, ?, ?)",
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
                    category VARCHAR,
                    label VARCHAR
                )
            """
            )
            self.conn.execute(
                """
                CREATE TABLE edges (
                    subject VARCHAR,
                    predicate VARCHAR,
                    object VARCHAR
                )
            """
            )

            # Import nodes
            print("Starting to import nodes...")
            start_time = time.time()
            self._import_nodes()

            elapsed_time_seconds = time.time() - start_time

            if elapsed_time_seconds >= 3600:
                elapsed_time_hours = elapsed_time_seconds / 3600
                print(f"Nodes import completed in {elapsed_time_hours:.2f} hours.")
            else:
                elapsed_time_minutes = elapsed_time_seconds / 60
                print(f"Nodes import completed in {elapsed_time_minutes:.2f} minutes.")

            # Import edges
            print("Starting to import edges...")
            start_time = time.time()
            self._import_edges()

            elapsed_time_seconds = time.time() - start_time
            if elapsed_time_seconds >= 3600:
                elapsed_time_hours = elapsed_time_seconds / 3600
                print(f"Edges import completed in {elapsed_time_hours:.2f} hours.")
            else:
                elapsed_time_minutes = elapsed_time_seconds / 60
                print(f"Edges import completed in {elapsed_time_minutes:.2f} minutes.")

            # Create indexes for faster querying
            print("Creating indexes...")
            start_time = time.time()
            self.conn.execute("CREATE INDEX idx_nodes_id ON nodes(id);")
            # self.conn.execute("CREATE INDEX idx_nodes_category ON nodes(category);")
            self.conn.execute("CREATE INDEX idx_edges_subject ON edges(subject);")
            # self.conn.execute("CREATE INDEX idx_edges_predicate ON edges(predicate);")
            self.conn.execute("CREATE INDEX idx_edges_object ON edges(object);")
            elapsed_time_seconds = time.time() - start_time
            if elapsed_time_seconds >= 3600:
                elapsed_time_hours = elapsed_time_seconds / 3600
                print(f"Index creation completed in {elapsed_time_hours:.2f} hours.")
            else:
                elapsed_time_minutes = elapsed_time_seconds / 60
                print(f"Index creation completed completed in {elapsed_time_minutes:.2f} minutes.")

            print("Import process finished.")

        return self.execute_unsafe_operation(_load_kg)

    def _import_nodes(self):
        columns_of_interest = ["id", "category", "name", "description"]
        nodes_filepath = Path(self.data_dir) / "nodes.tsv"

        with open(nodes_filepath, "r") as nodes_file:
            header_line = nodes_file.readline().strip().split("\t")
            column_indexes = {col: idx for idx, col in enumerate(header_line) if col in columns_of_interest}

            # Determine which label column to use
            label_column = "name" if "name" in column_indexes else "description"

            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_nodes_file:
                # Write the header line with the correct label column
                temp_nodes_file.write("\t".join(["id", "category", label_column]) + "\n")
                for line in nodes_file:
                    columns = line.strip().split("\t")
                    if len(columns) > max(column_indexes.values()):
                        node_id = columns[column_indexes["id"]]
                        node_category = columns[column_indexes["category"]]
                        node_label = columns[column_indexes[label_column]]
                        temp_nodes_file.write(f"{node_id}\t{node_category}\t{node_label}\n")
                temp_nodes_file.flush()

                # Load data from temporary file into DuckDB
                self.conn.execute(f"COPY nodes FROM '{temp_nodes_file.name}' (DELIMITER '\t', HEADER)")

    def _import_edges(self):
        edge_column_of_interest = ["subject", "predicate", "object"]
        edges_filepath = Path(self.data_dir) / "edges.tsv"
        with open(edges_filepath, "r") as edges_file:
            header_line = edges_file.readline().strip().split("\t")
            column_indexes = {col: idx for idx, col in enumerate(header_line) if col in edge_column_of_interest}

            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_edges_file:
                temp_edges_file.write("\t".join(edge_column_of_interest) + "\n")
                for line in edges_file:
                    columns = line.strip().split("\t")
                    subject = columns[column_indexes["subject"]]
                    predicate = columns[column_indexes["predicate"]]
                    object = columns[column_indexes["object"]]
                    temp_edges_file.write(f"{subject}\t{predicate}\t{object}\n")
                temp_edges_file.flush()

                # Load data from temporary file into DuckDB
                self.conn.execute(f"COPY edges FROM '{temp_edges_file.name}' (DELIMITER '\t', HEADER)")
