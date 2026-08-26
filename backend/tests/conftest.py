import asyncio
import os
from pathlib import Path

import httpx
import pytest

database_path = Path("/tmp/agentscope-pytest.db")
os.environ["AGENTSCOPE_DATABASE_URL"] = f"sqlite:///{database_path}"
os.environ["AGENTSCOPE_SEED_DEMO_DATA"] = "false"

from agentscope_server.database import Base, SessionLocal, engine  # noqa: E402
from agentscope_server.main import app  # noqa: E402
from agentscope_server.seed import seed_demo_data  # noqa: E402


class ASGIClient:
    def request(self, method: str, path: str, **kwargs):
        async def send():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as async_client:
                return await async_client.request(method, path, **kwargs)

        return asyncio.run(send())

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed_demo_data(session)
    yield ASGIClient()
    Base.metadata.drop_all(engine)
