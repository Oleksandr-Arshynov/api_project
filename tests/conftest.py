import asyncio
from datetime import datetime
import sys

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
sys.path.append(
    "/Users/oleksandrarshinov/Desktop/Documents/Repository/api_project/api_project/src"
)

from src.main import contacts_api
from src.auth.models import Base, ContactModel, UserModel
from src.database import get_db
from src.auth.service import auth_service

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)

TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

test_user = {"username": "deadpool", "email": "deadpool@example.com", "password": "12345678"}


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            hash_pass = auth_service.get_password_hash(test_user["password"])
            current_user = UserModel(username=test_user["username"], email=test_user["email"], hash_password=hash_pass,
                                confirmed=True)
            session.add(current_user)
            
        
            new_contact = ContactModel(
                    name="James config",
                    surname="Bond",
                    email="james_bond@gmail.com",
                    other=None,
                    user_id=current_user.id
                )
            session.add(new_contact)

            await session.commit()

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():
    # Dependency override

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        except Exception as err:
            print(err)
            await session.rollback()
        finally:
            await session.close()

    contacts_api.dependency_overrides[get_db] = override_get_db

    yield TestClient(contacts_api)


@pytest_asyncio.fixture()
async def get_token():
    token = await auth_service.create_access_token(payload={"sub": test_user["email"]})
    return token
