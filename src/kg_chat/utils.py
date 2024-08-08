"""Utility functions for the KG chatbot."""

import random
import webbrowser
from pathlib import Path

from langchain_core.prompts.prompt import PromptTemplate
from openai import OpenAI
from pyvis.network import Network

from kg_chat.config.llm_config import AnthropicConfig, CBORGConfig, LLMConfig, OllamaConfig, OpenAIConfig
from kg_chat.constants import (
    ANTHROPIC_KEY,
    ANTHROPIC_MODEL,
    CBORG_API_KEY,
    CBORG_MODEL,
    OLLAMA_MODEL,
    OPEN_AI_MODEL,
    OPENAI_KEY,
)

PREFIX_COLOR_MAP = {}


def extract_nodes_edges(structured_result):
    """Extract nodes and edges from the structured result."""
    nodes = structured_result.get("nodes", [])
    edges = structured_result.get("edges", [])

    return nodes, edges


# * LLM related utilities.**************************************************************************
def structure_query(query: str):
    """Structure the query to request structured results."""
    if "show me" in query.lower():
        # Modify the query to request structured results
        structured_query = f"""
        {query}
        Please provide the result in JSON format with ALL nodes and ALL edges. Return JSON ONLY.
        Property name MUST be enclosed in double quotes.
        IMPORTANT: I want nothing but pure JSON (verbose=False). Remove all unnecessary quotes and newlines.
        Example: {{
            "nodes": [
                {{"label": "A", "id": "1", category: "biolink:Gene"}},
                {{"label": "B", "id": "2", category: "biolink:ChemicalSubstance"}},
                {{"label": "C", "id": "3", category: "biolink:Disease"}},
                ..and so on
            ],
            "edges": [
                {{"subject": {{"label": "A", "id": "1"}},
                "object": {{"label": "B", "id": "2"}},
                "predicate": "biolink:related_to"}},
                ..and so on
            ]
        }}
        """
    else:
        structured_query = query
    return structured_query


def get_agent_prompt_template():
    """Get the agent prompt."""
    template = """
                You are an amazing Data Scientist that queries DuckDB databases by executing SQL queries
                 generated by yourself and return the results from those queries.
                You have access to additional tools like SQLDatabaseToolkit and QuerySQLDataBaseTool
                 in order to answer the following questions as best you can. DO NOT fabricate responses.
                 Any response should be strictly based on the information provided by the database via queries.
                Always answer in the same language as the user question. You have access to the following tools:

                {tools}

                To use a tool, please use the following format:

                '''
                "Thought": Do I need to use a tool? Yes.
                "Action 1": the action to take, should be one of [{tool_names}].
                "Action Input 1": the input to the action.
                "Observation": the result of the action.
                ... (this Thought/Action/Action Input/Observation can repeat 5 times)
                '''

                When the query returns the result use the format:
                '''
                "Thought": Do I need to use a tool? No
                "Final Answer": [your response here]
                '''

                Begin!

                Question: {input}
                Thought:{agent_scratchpad}
    """

    return PromptTemplate(
        input_variables=["input", "agent_scratchpad", "tools", "tool_names", "intermediate_steps"], template=template
    )


def get_llm_config(llm_provider: str, llm_model: str = None):
    """Get the LLM configuration based on the selected LLM."""

    def validate_and_get_model(provider, default_model, get_models_func):
        """Validate the model and get the model."""
        if llm_model is None:
            return default_model
        list_of_models = get_models_func()
        if llm_model not in list_of_models:
            raise ValueError(f"Model {llm_model} not supported. Please choose from {list_of_models}")
        return llm_model

    if llm_provider == "openai":
        from kg_chat.config.llm_config import OpenAIConfig

        llm_model = validate_and_get_model("openai", OPEN_AI_MODEL, get_openai_models)
        return OpenAIConfig(model=llm_model, api_key=OPENAI_KEY)

    elif llm_provider == "ollama":
        from kg_chat.config.llm_config import OllamaConfig

        llm_model = validate_and_get_model("ollama", OLLAMA_MODEL, get_ollama_models)
        return OllamaConfig(model=llm_model)

    elif llm_provider == "anthropic":
        from kg_chat.config.llm_config import AnthropicConfig

        llm_model = validate_and_get_model("anthropic", ANTHROPIC_MODEL, get_anthropic_models)
        return AnthropicConfig(model=llm_model, api_key=ANTHROPIC_KEY)

    elif llm_provider == "cborg":
        from kg_chat.config.llm_config import CBORGConfig

        llm_model = validate_and_get_model("cborg", CBORG_MODEL, get_lbl_cborg_models)
        return CBORGConfig(model=llm_model, api_key=CBORG_API_KEY)

    else:
        all_models = {
            "openai": get_openai_models(),
            "ollama": get_ollama_models(),
            "anthropic": get_anthropic_models(),
            "cborg": get_lbl_cborg_models(),
        }
        if llm_model is None:
            llm_model = OPEN_AI_MODEL
            from kg_chat.config.llm_config import OpenAIConfig

            return OpenAIConfig(model=llm_model, api_key=OPENAI_KEY)

        for provider, models in all_models.items():
            if llm_model in models:
                return get_llm_config(provider, llm_model)

        raise ValueError(f"Model {llm_model} not supported.")


def get_database_impl(database: str, data_dir: str, llm_config):
    """Get the database implementation based on the selected database."""
    if database == "neo4j":
        from kg_chat.implementations.neo4j_implementation import Neo4jImplementation

        return Neo4jImplementation(data_dir=data_dir, llm_config=llm_config)
    elif database == "duckdb":
        from kg_chat.implementations.duckdb_implementation import DuckDBImplementation

        return DuckDBImplementation(data_dir=data_dir, llm_config=llm_config)
    else:
        raise ValueError(f"Database {database} not supported.")


def llm_factory(config: LLMConfig):
    """Create an LLM instance based on the configuration."""
    if isinstance(config, OpenAIConfig):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=config.model, temperature=config.temperature, api_key=config.api_key)
    elif isinstance(config, OllamaConfig):
        from langchain_ollama import ChatOllama

        return ChatOllama(model=config.model, temperature=config.temperature, api_key=config.api_key)
    elif isinstance(config, AnthropicConfig):
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=config.model, temperature=config.temperature, api_key=config.api_key, max_tokens_to_sample=4096
        )
    elif isinstance(config, CBORGConfig):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=config.model, temperature=config.temperature, api_key=config.api_key, base_url=config.base_url
        )

    else:
        raise ValueError("Unsupported LLM configuration")


def get_openai_models():
    """Get the list of OpenAI models."""
    models_list = []
    if OPENAI_KEY != "None":
        openai = OpenAI()
        models_list = [model.id for model in openai.models.list() if model.id.startswith("gpt-4")]
    return models_list


def get_anthropic_models():
    """Get the list of Anthropic models."""
    return [
        "claude-3-5-sonnet-20240620",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]


def get_ollama_models():
    """Get the list of Ollama models."""
    return ["llama3.1"]


def get_lbl_cborg_models():
    """Get the list of LBNL-hosted models via CBORG."""
    return [
        "lbl/llama-3",  # LBNL-hosted model (free to use)
        "lbl/command-r-plus",  # LBNL-hosted model (free to use)
    ]


# * App related utilities. **************************************************************************
def generate_random_color():
    """Generate a random color."""
    while True:
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        if color not in PREFIX_COLOR_MAP.values():
            return color


def assign_color_to_prefix(curie):
    """Assign a color to a prefix."""
    prefix = curie.split(":")[0]
    if prefix not in PREFIX_COLOR_MAP:
        PREFIX_COLOR_MAP[prefix] = generate_random_color()
    # print(f"PREFIX_COLOR_MAP={PREFIX_COLOR_MAP}") # To debug
    return PREFIX_COLOR_MAP[prefix]


def visualize_kg(nodes, edges, app: bool = False, output_dir: str = None):
    """Visualize the knowledge graph using pyvis."""
    # Create a PyVis network
    net = Network(
        notebook=False,
        cdn_resources="in_line",
        neighborhood_highlight=True,
        select_menu=True,
        filter_menu=True,
    )

    if not nodes:
        print("No nodes to display.")
        return

    # Track added nodes to avoid duplicates
    added_nodes = set()

    # Add nodes to the network
    for node in nodes:
        # based on prefix (node["id"].split(":")[0]) assign nodes to color

        net.add_node(
            node["id"],
            label=node["label"],
            category=node.get("category", ""),
            title=node.get("id", ""),
            color=assign_color_to_prefix(node["id"]),
        )
        added_nodes.add(node["id"])

    # Add edges to the network
    for edge in edges:
        subject = edge["subject"]["id"]
        object = edge["object"]["id"]

        # Ensure both subject and object nodes are added
        if subject not in added_nodes:
            net.add_node(
                subject,
                label=edge["subject"].get("label", ""),
                category=edge["subject"].get("category", ""),
                title=subject,
                color=assign_color_to_prefix(subject),
            )
            added_nodes.add(subject)
        if object not in added_nodes:
            net.add_node(
                object,
                label=edge["object"].get("label", ""),
                category=edge["object"].get("category", ""),
                title=object,
                color=assign_color_to_prefix(object),
            )
            added_nodes.add(object)

        # Add edge with title (predicate)
        net.add_edge(subject, object, title=edge.get("predicate"))

    # Generate and display the network
    if output_dir:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
    else:
        output_dir_path = Path.cwd()
    html_file = str(output_dir_path / "knowledge_graph.html")
    net.show(html_file, notebook=False)

    # Open the generated HTML file in the default web browser
    webbrowser.open(html_file)
    if app:
        # Generate the HTML representation
        return net.generate_html()
