"""LLM abstraction layer supporting mock, Ollama, and OpenAI providers."""

import json
import os
from typing import Any, Optional

from pydantic import BaseModel


class LLMResponse(BaseModel):
    """LLM response model."""
    content: str
    tokens_used: int = 0
    provider: str = "mock"
    cached: bool = False


class LLMClient:
    """Abstracted LLM client with caching support.
    
    Supports:
    - mock: Deterministic template-based responses (no API calls)
    - ollama: Local Ollama server
    - openai: OpenAI API
    """
    
    def __init__(
        self,
        provider: str = "mock",
        max_tokens: int = 96,
        temperature: float = 0.7,
        cache: Optional[Any] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize LLM client.
        
        Args:
            provider: 'mock', 'ollama', or 'openai'
            max_tokens: Maximum tokens per response
            temperature: Response temperature
            cache: Cache instance for response caching
            api_key: API key for OpenAI
            base_url: Base URL for Ollama
        """
        self.provider = provider
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.cache = cache
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._client = None
    
    def _get_client(self):
        """Get provider-specific client."""
        if self.provider == "openai" and self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                pass
        return self._client
    
    def _make_cache_key(self, prompt: str, system: str) -> dict[str, Any]:
        """Create cache key data."""
        return {"prompt": prompt, "system": system, "max_tokens": self.max_tokens}
    
    def generate(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
        use_cache: bool = True,
    ) -> LLMResponse:
        """Generate text response.
        
        Args:
            prompt: User prompt
            system: System message
            use_cache: Whether to use cache
        
        Returns:
            LLMResponse instance
        """
        # Check cache first
        if use_cache and self.cache:
            cached = self.cache.get("llm", self._make_cache_key(prompt, system))
            if cached:
                return LLMResponse(
                    content=cached["content"],
                    tokens_used=cached.get("tokens_used", 0),
                    provider="cache",
                    cached=True,
                )
        
        # Generate based on provider
        if self.provider == "mock":
            response = self._mock_generate(prompt, system)
        elif self.provider == "ollama":
            response = self._ollama_generate(prompt, system)
        elif self.provider == "openai":
            response = self._openai_generate(prompt, system)
        else:
            response = self._mock_generate(prompt, system)
        
        # Cache response
        if use_cache and self.cache:
            self.cache.set("llm", self._make_cache_key(prompt, system), {
                "content": response.content,
                "tokens_used": response.tokens_used,
            })
        
        return response
    
    def _mock_generate(self, prompt: str, system: str) -> LLMResponse:
        """Generate mock response for testing."""
        # Template-based deterministic responses
        if "consumer" in system.lower() or "purchase" in prompt.lower():
            content = json.dumps({
                "action": "purchase",
                "confidence": 0.85,
                "reason": "Product matches preferences and budget",
                "utility_score": 0.78,
            }, indent=2)
            tokens = 30
        elif "competitor" in system.lower() or "response" in prompt.lower():
            content = json.dumps({
                "action": "discount",
                "confidence": 0.75,
                "reason": "Competitive pressure requires price adjustment",
                "impact_estimate": 0.15,
            }, indent=2)
            tokens = 28
        elif "analyst" in system.lower() or "market" in prompt.lower():
            content = json.dumps({
                "trend": "stable",
                "risk_level": "medium",
                "recommendation": "Monitor competitor actions",
            }, indent=2)
            tokens = 25
        else:
            content = json.dumps({
                "status": "ok",
                "message": "Processed successfully",
            }, indent=2)
            tokens = 15
        
        return LLMResponse(
            content=content,
            tokens_used=tokens,
            provider="mock",
        )
    
    def _ollama_generate(self, prompt: str, system: str) -> LLMResponse:
        """Generate response using Ollama."""
        import httpx
        
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {
                        "num_predict": self.max_tokens,
                        "temperature": self.temperature,
                    },
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data.get("response", ""),
                tokens_used=data.get("eval_count", 0),
                provider="ollama",
            )
        
        except Exception as e:
            # Fall back to mock on error
            return self._mock_generate(prompt, system)
    
    def _openai_generate(self, prompt: str, system: str) -> LLMResponse:
        """Generate response using OpenAI."""
        client = self._get_client()
        if client is None:
            return self._mock_generate(prompt, system)
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                tokens_used=response.usage.total_tokens if response.usage else 0,
                provider="openai",
            )
        
        except Exception:
            return self._mock_generate(prompt, system)
    
    def parse_json(self, response: LLMResponse) -> dict[str, Any]:
        """Parse JSON from LLM response.
        
        Args:
            response: LLM response
        
        Returns:
            Parsed dictionary
        """
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            match = re.search(r'\{[^}]+\}', response.content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return {}
