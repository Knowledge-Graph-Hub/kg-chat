Supported LLMs
==============

* OpenAI [default]
    .. note::
        The API key should be locally saved as an environment variable (`OPENAI_API_KEY`).
    * `kg-chat` is using `gpt-4o`

* Ollama (*Unreliable at the moment*): 
    * For this you will have to download the [Ollama application](https://ollama.com/download) and run it on your machine.
    * Then get the model of your choice by running the following command in the terminal:
        ```bash
        ollama pull llama3.1
        ```
    * `kg-chat` is using `llama3.1`
    .. note::
        As of now just the `qna` command works somewhat reliably. The `chat` or `app` commands don't work as expected.

* Anthropic:
.. note::
        The API key should be locally saved as an environment variable (`ANTHROPIC_API_KEY`).
    * `kg-chat` is using `claude-3-5-sonnet-20240620`
