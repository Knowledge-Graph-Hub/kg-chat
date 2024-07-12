"""Interface for the Database."""

from abc import ABC, abstractmethod


class DatabaseInterface(ABC):
    """Interface for the Database."""

    @abstractmethod
    def execute_query(self, query: str):
        """Execute a query against the database."""
        pass

    @abstractmethod
    def execute_query_using_langchain(self, query: str):
        """Execute a query against the database using Langchain."""
        pass

    @abstractmethod
    def load_kg(self):
        """Load the Knowledge Graph into the database."""
        pass

    @abstractmethod
    def show_schema(self):
        """Show the schema of the database."""
        pass

    @abstractmethod
    def get_human_response(self, query: str):
        """Get a human response from the database."""
        pass

    @abstractmethod
    def get_structured_response(self, query: str):
        """Get a structured response from the database."""
        pass

    @abstractmethod
    def clear_database(self, tx):
        """Clear the database."""
        pass

    @abstractmethod
    def create_nodes(self, nodes):
        """Create nodes in the database."""
        pass

    @abstractmethod
    def create_edges(self, edges):
        """Create edges in the database."""
        pass
