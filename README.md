# kg-chat

LLM-based chatbot that looks up information from  [`KGX`](https://github.com/biolink/kgx) nodes and edges TSV files loaded into either [`DuckDB`](https://github.com/duckdb/duckdb) (default) or [`neo4j`](https://github.com/neo4j/neo4j) database backend.

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
3. Replace [`data/nodes.tsv`](data/nodes.tsv) and [`data/edges.tsv`](data/edges.tsv) with desired KGX files if needed.

### Supported Backends
- DuckDB [default]
- Neo4j

### Commands

1. **Import KG**: Load nodes and edges into a database (default: duckdb).
    ```shell
    poetry run kg import
    ```

2. **Test Query**: Run a test query.
    ```shell
    poetry run kg test-query
    ```

3. **QnA**: Ask questions about the data.
    ```shell
    poetry run kg qna "how many nodes do we have here?"
    ```

4. **Chat**: Start an interactive chat session.
    ```shell
    poetry run kg chat
    ```

5. **App**: Deploy a local web application.
    ```shell
    poetry run kg app
    ```

### Visualization
Use `show me` in prompts for KG visualization.

---
### Acknowledgements

This [cookiecutter](https://cookiecutter.readthedocs.io/en/stable/README.html) project was developed from the [monarch-project-template](https://github.com/monarch-initiative/monarch-project-template) template and will be kept up-to-date using [cruft](https://cruft.github.io/cruft/).
