"""Command line interface for kg-chat."""

import logging
from pathlib import Path
from pprint import pprint
from typing import Union

import click

from kg_chat import __version__
from kg_chat.app import create_app
from kg_chat.constants import OPEN_AI_MODEL
from kg_chat.main import KnowledgeGraphChat
from kg_chat.utils import (
    get_anthropic_models,
    get_database_impl,
    get_lbl_cborg_models,
    get_llm_config,
    get_ollama_models,
    get_openai_models,
)

__all__ = [
    "main",
]

ALL_AVAILABLE_PROVIDERS = ["openai", "ollama", "anthropic", "cborg"]
ALL_AVAILABLE_MODELS = get_openai_models() + get_ollama_models() + get_anthropic_models() + get_lbl_cborg_models()
ALL_AVAILABLE_DB = ["neo4j", "duckdb"]

logger = logging.getLogger(__name__)
database_options = click.option(
    "--database",
    "-d",
    type=click.Choice(ALL_AVAILABLE_DB, case_sensitive=False),
    help="Database to use.",
    default="duckdb",
)
data_dir_option = click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing the data.",
    required=True,
)
llm_provider_option = click.option(
    "--llm-provider",
    type=click.Choice(ALL_AVAILABLE_PROVIDERS, case_sensitive=False),
    help="Language model to use.",
    required=False,
)
llm_option = click.option(
    "--llm",
    type=click.Choice(ALL_AVAILABLE_MODELS, case_sensitive=False),
    help="Language model to use.",
    required=False,
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
def list_models():
    """List the available language models."""
    click.echo(f"OpenAI models: {get_openai_models()}")
    click.echo(f"Anthropic models: {get_anthropic_models()}")
    click.echo(f"Ollama models: {get_ollama_models()}")
    click.echo(f"LBL-CBorg models: {get_lbl_cborg_models()}")


@main.command("import")
@database_options
@data_dir_option
@llm_provider_option
def import_kg(database: str = "duckdb", data_dir: str = None, llm_provider: str = "openai"):
    """Run the kg-chat's import command."""
    if not data_dir:
        raise ValueError("Data directory is required. This typically contains the KGX tsv files.")
    config = get_llm_config(llm_provider)
    impl = get_database_impl(database, data_dir=data_dir, llm_config=config)
    impl.load_kg()


@main.command()
@data_dir_option
@database_options
@llm_provider_option
@llm_option
def test_query(data_dir: Union[str, Path], llm_provider: str, llm: str, database: str = "duckdb"):
    """Run the kg-chat's test-query command."""
    if llm_provider is None and llm is None:
        llm = OPEN_AI_MODEL
    config = get_llm_config(llm_provider, llm)
    impl = get_database_impl(database, data_dir=data_dir, llm_config=config)

    query = "MATCH (n) RETURN n LIMIT 10" if database == "neo4j" else "SELECT * FROM nodes LIMIT 10"
    result = impl.execute_query(query)
    for record in result:
        print(record)


@main.command()
@data_dir_option
@database_options
@llm_provider_option
@llm_option
def show_schema(data_dir: Union[str, Path], llm_provider: str, llm: str, database: str = "duckdb"):
    """Run the kg-chat's show-schema command."""
    config = get_llm_config(llm_provider, llm)
    impl = get_database_impl(database, data_dir=data_dir, llm_config=config)
    impl.show_schema()


@main.command()
@database_options
@click.argument("query", type=str, required=True)
@data_dir_option
@llm_provider_option
@llm_option
def qna(query: str, data_dir: Union[str, Path], llm_provider: str, llm: str, database: str = "duckdb"):
    """Run the kg-chat's qna command."""
    config = get_llm_config(llm_provider, llm)
    impl = get_database_impl(database, data_dir=data_dir, llm_config=config)
    response = impl.get_human_response(query)
    pprint(response)


@main.command("chat")
@data_dir_option
@database_options
@llm_provider_option
@llm_option
def run_chat(data_dir: Union[str, Path], llm_provider: str, llm: str, database: str = "duckdb"):
    """Run the kg-chat's chat command."""
    config = get_llm_config(llm_provider, llm)
    impl = get_database_impl(database, data_dir=data_dir, llm_config=config)
    kgc = KnowledgeGraphChat(impl)
    kgc.chat()


@main.command("app")
@click.option("--debug", is_flag=True, help="Run the app in debug mode.")
@data_dir_option
@database_options
@llm_provider_option
@llm_option
def run_app(
    data_dir: Union[str, Path],
    llm_provider: str,
    llm: str,
    database: str = "duckdb",
    debug: bool = False,
):
    """Run the kg-chat's app command."""
    config = get_llm_config(llm_provider, llm)
    impl = get_database_impl(database, data_dir=data_dir, llm_config=config)
    kgc = KnowledgeGraphChat(impl)
    app = create_app(kgc)
    # use_reloader=False to avoid running the app twice in debug mode
    app.run(debug=debug, use_reloader=False)


if __name__ == "__main__":
    main()
