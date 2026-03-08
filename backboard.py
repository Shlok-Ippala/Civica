"""
Backboard SDK — async REST client for the Backboard AI API.

Base URL: https://app.backboard.io/api
Auth:     X-API-Key header

Endpoints used:
  POST /assistants
  POST /assistants/{assistant_id}/threads
  POST /threads/{thread_id}/messages
"""

import httpx


BASE_URL = "https://app.backboard.io/api"


class AssistantResponse:
    def __init__(self, data: dict):
        self.assistant_id: str = data["assistant_id"]
        self._data = data


class ThreadResponse:
    def __init__(self, data: dict):
        self.thread_id: str = data["thread_id"]
        self._data = data


class MessageResponse:
    def __init__(self, data: dict):
        self.content: str = data["content"]
        self._data = data


class BackboardClient:
    def __init__(self, api_key: str = ""):
        self._headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers=self._headers,
            timeout=120.0,
        )

    async def create_assistant(self, name: str, system_prompt: str) -> AssistantResponse:
        resp = await self._client.post(
            "/assistants",
            json={"name": name, "system_prompt": system_prompt},
        )
        resp.raise_for_status()
        return AssistantResponse(resp.json())

    async def create_thread(self, assistant_id: str) -> ThreadResponse:
        resp = await self._client.post(
            f"/assistants/{assistant_id}/threads",
            json={},
        )
        resp.raise_for_status()
        return ThreadResponse(resp.json())

    async def add_message(
        self,
        thread_id: str,
        content: str,
        llm_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        stream: bool = False,
    ) -> MessageResponse:
        resp = await self._client.post(
            f"/threads/{thread_id}/messages",
            json={
                "content": content,
                "llm_provider": llm_provider,
                "model_name": model_name,
                "stream": stream,
            },
        )
        resp.raise_for_status()
        return MessageResponse(resp.json())

    async def aclose(self):
        await self._client.aclose()
