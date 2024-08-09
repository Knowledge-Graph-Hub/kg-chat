Supported LLMs
==============

* OpenAI [default]
    .. note::
        The API key should be locally saved as an environment variable (`OPENAI_API_KEY`).
    * `kg-chat` is using `gpt-4o-mini`

* Ollama: 
    * For this you will have to download the `Ollama application <https://ollama.com/download>`_ and run it on your machine.
    * Then get the model of your choice by running the following command in the terminal:
        .. code:: bash
            ollama pull llama3.1
        
    * `kg-chat` is using `llama3.1`

    .. note::
        We highly recommend using the 405B model for decent results. Unless you have a powerful GPU, we do not recommend using this model.

* Anthropic:
    * `kg-chat` is using `claude-3-5-sonnet-20240620`

    .. note::
            The API key should be locally saved as an environment variable (`ANTHROPIC_API_KEY`).
        

* CBORG by LBNL:
    * `kg-chat` also supports `models offered Lawrence Berkeley National Laboratory (via CBORG)<https://cborg.lbl.gov/models/>`.
    * `kg-chat` is using `lbl/llama-3` which actually is llama3.1(405B).

    .. note::
            The API key should be locally saved as environment variable (`CBORG_API_KEY`).
        