"""Dash based app for the KG Chatbot."""

import json

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State

from kg_chat.cli import run_server
from kg_chat.main import get_human_response, get_structured_response
from kg_chat.utils import extract_nodes_edges, visualize_kg

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div(
    [
        dcc.Store(id="conversation-history"),
        # Main content area
        html.Div(
            id="main-content",
            children=[
                dcc.Loading(
                    id="loading",
                    type="default",
                    children=html.Iframe(id="graph-visualization", style={"width": "100%", "height": "600px"}),
                )
            ],
        ),
        # Chatbot interface at the bottom right corner
        html.Div(
            id="chat-interface",
            style={
                "position": "fixed",
                "bottom": "0",
                "right": "0",
                "width": "300px",
                "height": "400px",
                "border": "1px solid #ccc",
                "padding": "10px",
                "background-color": "#f9f9f9",
            },
            children=[
                dcc.Input(id="user-input", type="text", placeholder="Enter your prompt..."),
                html.Button("Submit", id="submit-button"),
                html.Div(id="chat-output"),
            ],
        ),
    ]
)


# Callback to handle user input and generate Cypher query
@app.callback(
    [
        Output("chat-output", "children"),
        Output("graph-visualization", "srcDoc"),
        Output("conversation-history", "data"),
        Output("user-input", "value"),
    ],
    [Input("submit-button", "n_clicks")],
    [State("user-input", "value"), State("conversation-history", "data")],
)
def update_output(n_clicks, value, history):
    """Update the chat output and graph visualization based on user input."""
    if n_clicks:
        if history is None:
            history = []

        try:

            if "show me" in value.lower():
                structured_response = get_structured_response(value)
                history.append(f"User: {value}\n")
                cleaned_result = structured_response.replace("```", "").replace("json\n", "").replace("\n", "")
                structured_result = json.loads(cleaned_result)
                nodes, edges = extract_nodes_edges(structured_result)
                html_str = visualize_kg(nodes, edges, app=True)
                if html_str:
                    return "\n".join(history), html_str, history, ""
            else:
                human_response = get_human_response(value)
                history.append(f"User: {value}\n\nBot: {human_response}\n")

            return "\n".join(history), "", history, ""

        except json.JSONDecodeError:
            history.append(f"User: {value}\nBot: Sorry, I could not understand the response format.")
            return "\n".join(history), "", history, ""
        except Exception as e:
            history.append(f"User: {value}\nBot: An error occurred: {e}")
            return "\n".join(history), "", history, ""

    return "", "", history, ""


# Run the app
if __name__ == "__main__":
    run_server()
