"""Command line interface for kg-chat."""

import logging
from pprint import pprint

import click

from kg_chat import __version__
from kg_chat.app import create_app
from kg_chat.implementations.duckdb_implementation import DuckDBImplementation
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
    default="duckdb",
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


@main.command("import")
@database_options
def import_kg(database: str = "duckdb"):
    """Run the kg-chat's demo command."""
    if database == "neo4j":
        impl = Neo4jImplementation(read_only=False)
        impl.load_kg()
    elif database == "duckdb":
        impl = DuckDBImplementation(read_only=False)
        impl.load_kg()
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command()
@database_options
def test_query(database: str = "duckdb"):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation()
        query = "MATCH (n) RETURN n LIMIT 10"
        result = impl.execute_query(query)
        for record in result:
            print(record)
    elif database == "duckdb":
        impl = DuckDBImplementation()
        query = "SELECT * FROM nodes LIMIT 10"
        result = impl.execute_query(query)
        for record in result:
            print(record)
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command()
@database_options
def show_schema(database: str = "duckdb"):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation()
        impl.show_schema()
    elif database == "duckdb":
        impl = DuckDBImplementation()
        impl.show_schema()
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command()
@database_options
@click.argument("query", type=str, required=True)
def qna(query: str, database: str = "duckdb"):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation()
        response = impl.get_human_response(query, impl)
        pprint(response)
    elif database == "duckdb":
        impl = DuckDBImplementation()
        response = impl.get_human_response(query)
        pprint(response)
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command("chat")
@database_options
def run_chat(database: str = "duckdb"):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation()
        kgc = KnowledgeGraphChat(impl)
        kgc.chat()
    elif database == "duckdb":
        impl = DuckDBImplementation()
        kgc = KnowledgeGraphChat(impl)
        kgc.chat()
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command("app")
@click.option("--debug", is_flag=True, help="Run the app in debug mode.")
@database_options
def run_app(
    debug: bool = False,
    database: str = "duckdb",
):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation()
        kgc = KnowledgeGraphChat(impl)
    elif database == "duckdb":
        impl = DuckDBImplementation()
        kgc = KnowledgeGraphChat(impl)
    else:
        raise ValueError(f"Database {database} not supported.")

    app = create_app(kgc)
    # use_reloader=False to avoid running the app twice in debug mode
    app.run(debug=debug, use_reloader=False)


if __name__ == "__main__":
    main()
