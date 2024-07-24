"""Command line interface for kg-chat."""

import logging
from pathlib import Path
from pprint import pprint
from typing import Union

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
data_dir_option = click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing the data.",
    required=True,
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
@data_dir_option
def import_kg(database: str = "duckdb", data_dir: str = None):
    """Run the kg-chat's demo command."""
    if not data_dir:
        raise ValueError("Data directory is required. This typically contains the KGX tsv files.")
    if database == "neo4j":
        impl = Neo4jImplementation(data_dir=data_dir)
        impl.load_kg()
    elif database == "duckdb":
        impl = DuckDBImplementation(data_dir=data_dir)
        impl.load_kg()
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command()
@data_dir_option
@database_options
def test_query(data_dir: Union[str, Path], database: str = "duckdb"):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation(data_dir=data_dir)
        query = "MATCH (n) RETURN n LIMIT 10"
        result = impl.execute_query(query)
        for record in result:
            print(record)
    elif database == "duckdb":
        impl = DuckDBImplementation(data_dir=data_dir)
        query = "SELECT * FROM nodes LIMIT 10"
        result = impl.execute_query(query)
        for record in result:
            print(record)
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command()
@data_dir_option
@database_options
def show_schema(data_dir: Union[str, Path], database: str = "duckdb"):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation(data_dir=data_dir)
        impl.show_schema()
    elif database == "duckdb":
        impl = DuckDBImplementation(data_dir=data_dir)
        impl.show_schema()
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command()
@database_options
@click.argument("query", type=str, required=True)
@data_dir_option
def qna(query: str, data_dir: Union[str, Path], database: str = "duckdb"):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation(data_dir=data_dir)
        response = impl.get_human_response(query, impl)
        pprint(response)
    elif database == "duckdb":
        impl = DuckDBImplementation(data_dir=data_dir)
        response = impl.get_human_response(query)
        pprint(response)
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command("chat")
@data_dir_option
@database_options
def run_chat(data_dir: Union[str, Path], database: str = "duckdb"):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation(data_dir=data_dir)
        kgc = KnowledgeGraphChat(impl)
        kgc.chat()
    elif database == "duckdb":
        impl = DuckDBImplementation(data_dir=data_dir)
        kgc = KnowledgeGraphChat(impl)
        kgc.chat()
    else:
        raise ValueError(f"Database {database} not supported.")


@main.command("app")
@click.option("--debug", is_flag=True, help="Run the app in debug mode.")
@data_dir_option
@database_options
def run_app(
    data_dir: Union[str, Path],
    debug: bool = False,
    database: str = "duckdb",
):
    """Run the kg-chat's chat command."""
    if database == "neo4j":
        impl = Neo4jImplementation(data_dir=data_dir)
        kgc = KnowledgeGraphChat(impl)
    elif database == "duckdb":
        impl = DuckDBImplementation(data_dir=data_dir)
        kgc = KnowledgeGraphChat(impl)
    else:
        raise ValueError(f"Database {database} not supported.")

    app = create_app(kgc)
    # use_reloader=False to avoid running the app twice in debug mode
    app.run(debug=debug, use_reloader=False)


if __name__ == "__main__":
    main()
