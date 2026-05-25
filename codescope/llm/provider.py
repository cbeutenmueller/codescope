from __future__ import annotations
from openai import AsyncOpenAI
from codescope.config import LLMProfile


class LLMProvider:
    def __init__(self, profile: LLMProfile) -> None:
        self._profile = profile
        self._client = AsyncOpenAI(
            api_key=profile.api_key,
            base_url=profile.base_url,
            timeout=profile.timeout,
        )

    async def complete(self, messages: list[dict], *, max_tokens: int = 2000) -> str:
        response = await self._client.chat.completions.create(
            model=self._profile.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    async def complete_json(self, messages: list[dict], *, max_tokens: int = 2000) -> str:
        response = await self._client.chat.completions.create(
            model=self._profile.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or "{}"
