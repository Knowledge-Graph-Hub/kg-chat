"""Command line interface for kg-chat."""

import logging

import click

from kg_chat import __version__
from kg_chat.main import chat, execute_query_using_langchain, load_neo4j, question_and_answer

__all__ = [
    "main",
]

logger = logging.getLogger(__name__)


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
def import_kg():
    """Run the kg-chat's demo command."""
    load_neo4j()


@main.command()
def test_query():
    """Run the kg-chat's chat command."""
    # Example query to get all nodes
    query = "MATCH (n) RETURN n LIMIT 10"
    result = execute_query_using_langchain(query)

    # Print the results
    for record in result:
        print(record)


@main.command()
def show_schema():
    """Run the kg-chat's chat command."""
    # Example query to get all nodes
    query = "CALL db.schema.visualization()"
    result = execute_query_using_langchain(query)

    # Print the results
    for record in result:
        print(record)


@main.command()
@click.argument("query", type=str, required=True)
def qna(query: str):
    """Run the kg-chat's chat command."""
    question_and_answer(query)


@main.command()
def start_chat():
    """Run the kg-chat's chat command."""
    chat()


if __name__ == "__main__":
    main()
