"""Dash based app for the KG Chatbot."""

import io
import json
import zipfile

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State

from kg_chat.main import KnowledgeGraphChat
from kg_chat.utils import extract_nodes_edges, visualize_kg

# Global variable to store the last structured result
LAST_STRUCTURED_RESULT = None


def create_app(kg_chatbot: KnowledgeGraphChat):
    """Create a Dash app for the KG Chatbot."""
    # Initialize the Dash app
    app = dash.Dash(__name__, title="KG Chatbot")

    # Define the layout of the app
    app.layout = html.Div(
        [
            dcc.Store(id="conversation-history"),
            # Main content area
            html.Div(
                id="main-content",
                children=[
                    html.H1("KG Chat", style={"textAlign": "center"}),  # Add title here
                    dcc.Loading(
                        id="loading",
                        type="default",
                        children=html.Iframe(
                            id="graph-visualization",
                        ),
                    ),
                ],
            ),
            # Chatbot interface at the bottom right corner
            html.Div(
                id="chat-interface",
                children=[
                    html.Div(id="chat-output", style={"overflowY": "auto", "maxHeight": "300px"}),
                    dcc.Input(id="user-input", type="text", placeholder="Enter your prompt...", n_submit=0),
                    html.Button("Submit", id="submit-button"),
                    html.Button("Reset", id="reset-button", style={"margin-left": "10px"}),
                    html.Button("Download", id="download-button", style={"margin-left": "10px"}),
                    dcc.Download(id="download-results"),
                ],
            ),
        ]
    )

    def update_output(submit_n_clicks, reset_n_clicks, n_submit, value, history, kg_chatbot):
        """Update the chat output and graph visualization based on user input."""
        ctx = dash.callback_context

        if not ctx.triggered:
            return "", "", history, ""

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if (button_id == "submit-button" and submit_n_clicks) or (button_id == "user-input" and n_submit):
            if history is None:
                history = []

            try:
                if "show me" in value.lower():
                    structured_response = kg_chatbot.get_structured_response(value)
                    history.append(f"User: {value}")
                    cleaned_result = structured_response.replace("```", "").replace("json\n", "").replace("\n", "")
                    structured_result = json.loads(cleaned_result)
                    global LAST_STRUCTURED_RESULT
                    LAST_STRUCTURED_RESULT = structured_result  # Store the structured result
                    nodes, edges = extract_nodes_edges(structured_result)
                    html_str = visualize_kg(nodes, edges, app=True)
                    if html_str:
                        return [html.P(line) for line in history], html_str, history, ""
                else:
                    human_response = kg_chatbot.get_human_response(value)
                    history.append(f"User: {value}")
                    history.append(f"Bot: {human_response}")

                return [html.P(line) for line in history], "", history, ""

            except json.JSONDecodeError:
                history.append(f"User: {value}")
                history.append("Bot: Sorry, I could not understand the response format.")
                return [html.P(line) for line in history], "", history, ""
            except Exception as e:
                history.append(f"User: {value}")
                history.append(f"Bot: An error occurred: {e}")
                return [html.P(line) for line in history], "", history, ""

        elif button_id == "reset-button" and reset_n_clicks:
            return "", "", [], ""

        return "", "", history, ""

    @app.callback(
        Output("download-results", "data"),
        [Input("download-button", "n_clicks")],
        [State("conversation-history", "data")],
        prevent_initial_call=True,
    )
    def download_results(n_clicks, history):
        """Download the nodes and edges as a zip file."""
        if not history:
            return None

        # Extract nodes and edges from the last structured response in the history
        try:
            last_response = LAST_STRUCTURED_RESULT
            if not last_response:
                return None

            nodes, edges = extract_nodes_edges(last_response)
            # Convert nodes and edges to TSV strings
            nodes_tsv = "id\tcategory\tlabel\n" + "\n".join(
                [f"{node['id']}\t{node['category']}\t{node['label']}" for node in nodes]
            )
            edges_tsv = "subject\tpredicate\tobject\n" + "\n".join(
                [f"{edge['subject']['id']}\t{edge['predicate']}\t{edge['object']['id']}" for edge in edges]
            )

            # Create a BytesIO buffer to hold the zip file
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as zf:
                # Write nodes.tsv
                zf.writestr("nodes.tsv", nodes_tsv.encode("utf-8"))

                # Write edges.tsv
                zf.writestr("edges.tsv", edges_tsv.encode("utf-8"))

            buffer.seek(0)
            return dcc.send_bytes(buffer.getvalue(), "kg-subset.zip")

        except Exception as e:
            print(f"Error generating download: {e}")
            return None

    # Wrapper function to pass the database instance to the callback
    @app.callback(
        [
            Output("chat-output", "children"),
            Output("graph-visualization", "srcDoc"),
            Output("conversation-history", "data"),
            Output("user-input", "value"),
        ],
        [Input("submit-button", "n_clicks"), Input("reset-button", "n_clicks"), Input("user-input", "n_submit")],
        [State("user-input", "value"), State("conversation-history", "data")],
    )
    def _wrapped_update_output(submit_n_clicks, reset_n_clicks, n_submit, value, history):
        return update_output(submit_n_clicks, reset_n_clicks, n_submit, value, history, kg_chatbot)

    return app
