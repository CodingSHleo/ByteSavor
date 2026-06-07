import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest_asyncio.fixture(loop_scope="session")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
