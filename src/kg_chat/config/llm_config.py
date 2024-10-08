"""Configuration for the LLM model."""

from pydantic import BaseModel


class LLMConfig(BaseModel):
    """Configuration for the LLM model."""

    model: str
    api_key: str = None
    temperature: float = 0.0


class OpenAIConfig(LLMConfig):
    """Configuration for OpenAI LLM model."""

    def __init__(self, **data):
        """Initialize the OpenAI LLM configuration."""
        super().__init__(**data)
        if self.model.startswith("o1"):
            self.temperature = 1.0


class OllamaConfig(LLMConfig):
    """Configuration for Ollama LLM model."""

    format: str = None
    pass


class AnthropicConfig(LLMConfig):
    """Configuration for Anthropic LLM model."""

    pass


class CBORGConfig(LLMConfig):
    """Configuration for CBORG LLM model."""

    base_url: str = "https://api.cborg.lbl.gov"  # Local clients can also use https://api-local.cborg.lbl.gov
