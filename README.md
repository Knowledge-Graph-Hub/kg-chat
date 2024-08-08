# kg-chat

LLM-based chatbot that queries and visualizes [`KGX`](https://github.com/biolink/kgx) nodes and edges TSV files loaded into either [`DuckDB`](https://github.com/duckdb/duckdb) (default) or [`neo4j`](https://github.com/neo4j/neo4j) database backend.

Certainly! Here's a more concise version:

## LLMs Supported

- **OpenAI**
  > **_NOTE:_** Ensure `OPENAI_API_KEY` is set as an environment variable.

- **Anthropic**
  > **_NOTE:_** Ensure `ANTHROPIC_API_KEY` is set as an environment variable.

- **Ollama**
  > **_NOTE:_** Currently throws error: `Invalid Format: Missing 'Action:' after 'Thought'` as of now. Work in progress...
  - No API key required.
  - Download the application from [here](https://ollama.com/download).
  - Get the model by running:
    ```shell
        ollama pull llama3.1 
    ```
- **Models hosted by Lawrence Berkeley National Laboratory vi CBORG**
  > **_NOTE:_** Ensure `CBORG_API_KEY` is set as an environment variable.
  - The list of modes can be found (here)[https://cborg.lbl.gov/models/] listed under "LBNL_Hosted Models".
  - The only LLMs that work for now:
    - `lbl/llama-3` (actually llama3.1(405B))
    - `openai/gpt-4o-mini`
    - `anthropic/claude-haiku`
    - `anthropic/claude-sonnet`
    - `anthropic/claude-opus`


#### How to set the API key as an environment variable?
One quick way is 
```shell
    export OPENAI_API_KEY=XXXXXX
    export ANTHROPIC_API_KEY=XXXXX
```
But if you want these to persist permanently
```shell
    vi ~/.bash_profile
```

OR

```
    vi ~/.bashrc
```
Add the 2 lines exporting the variables above and then
```shell
    source ~/.bash_profile
```
OR
```
    source ~/.bashrc
```

## Setup

### For Neo4j Backend (Optional)
1. Install Neo4j desktop from [here](https://neo4j.com/download/).
2. Create a new project and database, then start it.
3. Install the APOC plugin in Neo4j Desktop.
4. Update settings to match [`neo4j_db_settings.conf`](conf_files/neo4j_db_settings.conf).

### General Setup 

#### For Developers 
1. Clone this repository.
2. Create a virtual environment and install dependencies:
    ```shell
    cd kg-chat
    pip install poetry
    poetry install
    ```
3. Replace [`data/nodes.tsv`](data/nodes.tsv) and [`data/edges.tsv`](data/edges.tsv) with desired KGX files if needed.

### For using kg-chat as a dependency

```shell
pip install kg-chat
```
OR
```shell
poetry add kg-chat@latest
```

### Supported Backends
- DuckDB [default]
- Neo4j

### Commands

1. **Import KG**: Load nodes and edges into a database (default: duckdb).
    ```shell
    poetry run kg import --data-dir data
    ```

2. **Test Query**: Run a test query. 
   > NOTE: `--data-dir` is a required parameter for all commands. This is the path for the directory which contains the nodes.tsv and edges.tsv file. The filenames are expected to be exactly that.
    ```shell
    poetry run kg test-query --data-dir data
    ```

3. **QnA**: Ask questions about the data.
    ```shell
    poetry run kg qna "how many nodes do we have here?" --data-dir data
    ```

4. **Chat**: Start an interactive chat session.
    ```shell
    poetry run kg chat --data-dir data
    ```

5. **App**: Deploy a local web application.
    ```shell
    poetry run kg app --data-dir data
    ```

### Visualization
Use `show me` in prompts for KG visualization.

---
### Acknowledgements

This [cookiecutter](https://cookiecutter.readthedocs.io/en/stable/README.html) project was developed from the [monarch-project-template](https://github.com/monarch-initiative/monarch-project-template) template and will be kept up-to-date using [cruft](https://cruft.github.io/cruft/).
