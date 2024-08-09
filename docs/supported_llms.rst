Supported LLMs
==============

* OpenAI [default]
    .. note::
        The API key should be locally saved as an environment variable (```OPENAI_API_KEY```).
    * ```kg-chat``` uses ```gpt-4o-mini``` by default.

* Ollama: 
    * For this you will have to download the `Ollama application <https://ollama.com/download>`_ and run it on your machine.
    * Then get the model of your choice by running the following command in the terminal:

        .. code-block:: bash

            ollama run llama3.1:405b

    .. note::
        The results are not very good with the 8b model.
        We recommend using the 405b model for decent results.
        GPU is recommended for faster results.

* Anthropic:
    * ```kg-chat``` uses ```claude-3-5-sonnet-20240620``` by default.

    .. note::
            The API key should be locally saved as an environment variable (```ANTHROPIC_API_KEY```).
        

* CBORG by LBNL:
    * ```kg-chat``` also supports `models offered Lawrence Berkeley National Laboratory (via CBORG) <https://cborg.lbl.gov/models/>`_.
    * ```kg-chat``` uses ```lbl/llama-3``` by default which actually is llama3.1(405B).

    .. note::
            The API key should be locally saved as environment variable (```CBORG_API_KEY```).
        