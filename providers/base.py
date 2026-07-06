"""
Arkadia Knowledge OS — Provider Base Interface
===============================================
Every AI provider MUST implement this interface.
Business logic is NEVER inside a provider adapter.
Providers only implement: authenticate, send, stream, history, attachments, models, capabilities, health.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class ProviderMessage:
    """Canonical message format, provider-agnostic."""
    def __init__(self, role: str, content: str):
        self.role = role      # "user" | "assistant" | "system"
        self.content = content

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class ProviderResponse:
    """Canonical response envelope from any provider."""
    def __init__(
        self,
        content: str,
        model: str,
        provider_name: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        raw: Optional[dict] = None,
    ):
        self.content = content
        self.model = model
        self.provider_name = provider_name
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.raw = raw or {}

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider_name,
            "usage": {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.prompt_tokens + self.completion_tokens,
            },
        }


class BaseProvider(ABC):
    """
    Abstract base for all Arkadia AI provider adapters.
    Arkadia's business logic must NEVER depend on provider-specific behaviour.
    Add a new provider by implementing this class and registering it in the router.
    """

    name: str = "base"
    display_name: str = "Base Provider"

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Verify that credentials are available and valid.
        Returns True if the provider is ready to accept calls.
        """

    @abstractmethod
    def send(
        self,
        messages: list[ProviderMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> ProviderResponse:
        """
        Send a synchronous chat request.
        Returns a ProviderResponse.
        """

    @abstractmethod
    def stream(
        self,
        messages: list[ProviderMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream a chat response token by token.
        Yields string chunks.
        """

    def history(self, thread_id: str) -> list[dict]:
        """
        Return conversation history for a thread, if the provider supports it.
        Default: return empty list (stateless providers).
        """
        return []

    def attachments(self, file_path: str) -> Optional[dict]:
        """
        Upload or reference an attachment.
        Returns provider-specific attachment descriptor or None.
        """
        return None

    @abstractmethod
    def models(self) -> list[str]:
        """Return the list of available model IDs for this provider."""

    @abstractmethod
    def capabilities(self) -> list[str]:
        """
        Return the capability list.
        Valid values: "chat", "stream", "embed", "vision", "function_call", "search"
        """

    @abstractmethod
    def health(self) -> dict:
        """
        Return health/status info.
        Must include: {"status": "ok"|"error"|"unconfigured", "model": str, "latency_ms": int}
        """
