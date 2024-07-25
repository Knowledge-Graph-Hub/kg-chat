"""Command line interface for kg-chat."""

import logging
from pathlib import Path
from pprint import pprint
from typing import Union

import click

from kg_chat import __version__
from kg_chat.app import create_app
from kg_chat.constants import OLLAMA_MODEL, OPEN_AI_MODEL, OPENAI_KEY
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
llm_option = click.option(
    "--llm",
    type=click.Choice(["openai", "ollama"], case_sensitive=False),
    default="openai",
    help="Language model to use.",
    required=False,
)


def get_llm_config(llm: str):
    """Get the LLM configuration based on the selected LLM."""
    if llm == "openai":
        from kg_chat.config.llm_config import OpenAIConfig

        return OpenAIConfig(model=OPEN_AI_MODEL, api_key=OPENAI_KEY)
    elif llm == "ollama":
        from kg_chat.config.llm_config import OllamaConfig

        return OllamaConfig(model=OLLAMA_MODEL)
    else:
        raise ValueError(f"LLM {llm} not supported.")


def get_database_impl(database: str, data_dir: str, llm_config):
    """Get the database implementation based on the selected database."""
    if database == "neo4j":
        return Neo4jImplementation(data_dir=data_dir, llm_config=llm_config)
    elif database == "duckdb":
        return DuckDBImplementation(data_dir=data_dir, llm_config=llm_config)
    else:
        raise ValueError(f"Database {database} not supported.")


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
@llm_option
def import_kg(database: str = "duckdb", data_dir: str = None, llm: str = "openai"):
    """Run the kg-chat's demo command."""
    if not data_dir:
        raise ValueError("Data directory is required. This typically contains the KGX tsv files.")
    config = get_llm_config(llm)
    impl = get_database_impl(database, data_dir=data_dir, llm_config=config)
    impl.load_kg()


@main.command()
@data_dir_option
@database_options
@llm_option
def test_query(data_dir: Union[str, Path], database: str = "duckdb", llm: str = "openai"):
    """Run the kg-chat's chat command."""
    config = get_llm_config(llm)
    impl = get_database_impl(database, data_dir=data_dir, llm_config=config)

    query = "MATCH (n) RETURN n LIMIT 10" if database == "neo4j" else "SELECT * FROM nodes LIMIT 10"
    result = impl.execute_query(query)
    for record in result:
        print(record)


@main.command()
@data_dir_option
@database_options
@llm_option
def show_schema(data_dir: Union[str, Path], database: str = "duckdb", llm: str = "openai"):
    """Run the kg-chat's chat command."""
    config = get_llm_config(llm)
    impl = get_database_impl(database, data_dir=data_dir, llm_config=config)
    impl.show_schema()


@main.command()
@database_options
@click.argument("query", type=str, required=True)
@data_dir_option
@llm_option
def qna(query: str, data_dir: Union[str, Path], database: str = "duckdb", llm: str = "openai"):
    """Run the kg-chat's chat command."""
    config = get_llm_config(llm)
    impl = get_database_impl(database, data_dir=data_dir, llm_config=config)
    response = impl.get_human_response(query)
    pprint(response)


@main.command("chat")
@data_dir_option
@database_options
@llm_option
def run_chat(data_dir: Union[str, Path], database: str = "duckdb", llm: str = "openai"):
    """Run the kg-chat's chat command."""
    config = get_llm_config(llm)
    impl = get_database_impl(database, data_dir=data_dir, llm_config=config)
    kgc = KnowledgeGraphChat(impl)
    kgc.chat()


@main.command("app")
@click.option("--debug", is_flag=True, help="Run the app in debug mode.")
@data_dir_option
@database_options
@llm_option
def run_app(
    data_dir: Union[str, Path],
    debug: bool = False,
    database: str = "duckdb",
    llm: str = "openai",
):
    """Run the kg-chat's chat command."""
    config = get_llm_config(llm)
    impl = get_database_impl(database, data_dir=data_dir, llm_config=config)
    kgc = KnowledgeGraphChat(impl)
    app = create_app(kgc)
    # use_reloader=False to avoid running the app twice in debug mode
    app.run(debug=debug, use_reloader=False)


if __name__ == "__main__":
    main()
