"""Configuration for the LLM model."""

from pydantic import BaseModel


class LLMConfig(BaseModel):
    """Configuration for the LLM model."""

    model: str
    api_key: str = None
    temperature: float = 0.0


class OpenAIConfig(LLMConfig):
    """Configuration for OpenAI LLM model."""

    pass


class OllamaConfig(LLMConfig):
    """Configuration for Ollama LLM model."""

    pass


class AnthropicConfig(LLMConfig):
    """Configuration for Anthropic LLM model."""

    pass
