from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from . import config

# Create async engine for PostgreSQL
engine = create_async_engine(
    config.DB_URL,
    echo=True,
    poolclass=NullPool,  # Use NullPool for async operations
    future=True
)

async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        raise

async def get_session():
    """Get database session."""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

