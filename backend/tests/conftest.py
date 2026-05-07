"""Fixtures pytest per il backend OSM Broker.
Redis viene sostituito con un fake in-memory per i test CI.
"""
import os
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("AUTH_ENABLED", "false")
os.environ.setdefault("MAX_AREA_KM2", "500")
os.environ.setdefault("RATELIMIT_ENABLED", "False")
import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Fake Redis in-memory ───────────────────────────────────────────────────

class FakeRedis:
    """Redis asincrono minimale per i test (nessun server necessario)."""

    def __init__(self):
        self._store: dict[str, str] = {}
        self._queues: dict[str, list[str]] = {}

    async def ping(self) -> bool:
        return True

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def rpush(self, queue: str, value: str) -> None:
        self._queues.setdefault(queue, []).append(value)

    async def blpop(self, queue: str, timeout: int = 0):
        q = self._queues.get(queue, [])
        if q:
            return (queue, q.pop(0))
        return None

    async def aclose(self) -> None:  # compatibilità redis-py
        pass


_fake_redis = FakeRedis()


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """
    Sostituisce il client Redis reale con FakeRedis.
    Applicato automaticamente a tutti i test.
    """
    import app.store as store_module

    monkeypatch.setattr(store_module, "_client", _fake_redis)

    # Pulisce lo store tra un test e l'altro
    _fake_redis._store.clear()
    _fake_redis._queues.clear()

    yield _fake_redis
