# kg-chat

Chatbot that looks up information from provided [`KGX`](https://github.com/biolink/kgx) files (nodes and edges TSV files). It uses [`langchain`](https://github.com/langchain-ai/langchain) and [`DuckDB`](https://github.com/duckdb/duckdb) (default) or [`neo4j`](https://github.com/neo4j/neo4j).

> **_NOTE:_**  
> Ensure `OPENAI_API_KEY` is set as an environmental variable.

## Setup

### For Neo4j Backend (Optional)
1. Install Neo4j desktop from [here](https://neo4j.com/download/).
2. Create a new project and database, then start it.
3. Install the APOC plugin in Neo4j Desktop.
4. Update settings to match [`neo4j_db_settings.conf`](conf_files/neo4j_db_settings.conf).

### General Setup
1. Clone this repository.
2. Create a virtual environment and install dependencies:
    ```shell
    cd kg-chat
    pip install poetry
    poetry install
    ```
3. Replace [`data/nodes.tsv`](src/kg_chat/data/nodes.tsv) and [`data/edges.tsv`](src/kg_chat/data/edges.tsv) with corresponding KGX files.

### Supported Backends
- DuckDB [default]
- Neo4j

### Commands

1. **Import KG**: Load nodes and edges into Neo4j.
    ```shell
    kg import
    ```

2. **Test Query**: Run a test query.
    ```shell
    kg test-query
    ```

3. **QnA**: Ask questions about the data.
    ```shell
    kg qna "your question here"
    ```

4. **Chat**: Start an interactive chat session.
    ```shell
    kg chat
    ```

5. **App**: Deploy a local web application.
    ```shell
    kg app
    ```

### Visualization
Use `show me` in prompts for KG representation.

---
### Acknowledgements

This [cookiecutter](https://cookiecutter.readthedocs.io/en/stable/README.html) project was developed from the [monarch-project-template](https://github.com/monarch-initiative/monarch-project-template) template and will be kept up-to-date using [cruft](https://cruft.github.io/cruft/).
