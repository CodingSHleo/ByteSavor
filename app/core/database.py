from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

url = (
    f"mysql+asyncmy://{settings.mysql_user}:{quote_plus(settings.mysql_password)}"
    f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_db}"
    "?charset=utf8mb4"
)

engine = create_async_engine(url, echo=settings.debug, pool_size=10, max_overflow=20)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
