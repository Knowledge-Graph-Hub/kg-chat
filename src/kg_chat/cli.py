"""Command line interface for kg-chat."""

import logging

import click

from kg_chat import __version__
from kg_chat.app import create_app
from kg_chat.implementations.neo4j_implementation import Neo4jImplementation
from kg_chat.main import KnowledgeGraphChat

__all__ = [
    "main",
]

logger = logging.getLogger(__name__)
database_options = click.option(
    "--database",
    "-d",
    type=click.Choice(["neo4j", "duckdb"], case_sensitive=False),
    help="Database to use.",
    default="neo4j",
)


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
@click.version_option(__version__)
def main(verbose: int, quiet: bool):
    """
    CLI for kg-chat.

    :param verbose: Verbosity while running.
    :param quiet: Boolean to be quiet or verbose.
    """
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)


@main.command()
@database_options
def import_kg(database: str = "neo4j"):
    """Run the kg-chat's demo command."""
    if database == "neo4j":
        impl = Neo4jImplementation()
        impl.load_kg()
    elif database == "duckdb":
        raise NotImplementedError("DuckDB not implemented yet.")
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command()
@database_options
def test_query(database: str = "neo4j"):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation()
        query = "MATCH (n) RETURN n LIMIT 10"
        result = impl.execute_query(query)
        for record in result:
            print(record)
    elif database == "duckdb":
        raise NotImplementedError("DuckDB not implemented yet.")
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command()
@database_options
def show_schema(database: str = "neo4j"):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation()
        impl.show_schema()
    elif database == "duckdb":
        raise NotImplementedError("DuckDB not implemented yet.")
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command()
@database_options
@click.argument("query", type=str, required=True)
def qna(query: str, database: str = "neo4j"):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation()
        response = impl.get_human_response(query, impl)
        print(response)
    elif database == "duckdb":
        raise NotImplementedError("DuckDB not implemented yet.")
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command()
@database_options
def run_chat(database: str = "neo4j"):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation()
        kgc = KnowledgeGraphChat(impl)
        kgc.chat()
    elif database == "duckdb":
        raise NotImplementedError("DuckDB not implemented yet.")
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command()
@click.option("--debug", is_flag=True, help="Run the app in debug mode.")
@database_options
def run_app(
    debug: bool = False,
    database: str = "neo4j",
):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation()
        kgc = KnowledgeGraphChat(impl)
    elif database == "duckdb":
        raise NotImplementedError("DuckDB not implemented yet.")
    else:
        raise ValueError(f"Database {database} not supported.")

    app = create_app(kgc)
    app.run_server(debug=debug)


if __name__ == "__main__":
    main()
