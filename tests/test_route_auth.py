from unittest.mock import Mock

import pytest
from sqlalchemy import select

from src.conf import messages
from src.auth.models import UserModel
from tests.conftest import TestingSessionLocal

user_data = {"username": "test_username", "email": "test_email@example.com", "password": "12345678"}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()  # автоматично створить мок-об'єкт з усіма необхідними методами та атрибутами, включно з await, який використовується у функції send_email.
    monkeypatch.setattr("src.auth.email.send_email", mock_send_email)  # Метод monkeypatch.setattr підміняє виклик функції send_email з модуля src.routes.auth на мок-об'єкт mock_send_email.
    response = client.post("/auth/signup", json=user_data)  # Далі client.post виконує POST-запит на вказану URL-адресу /api/auth/signup, передаючи в тілі запиту JSON-представлення даних користувача user.
    assert response.status_code == 201, response.text  #  переконуємося, що код стану відповіді сервера дорівнює 201 (успішне створення ресурсу)
    data = response.json()  # Перевіряємо дані, що повертаються
    assert data["username"] == user_data["username"]  # Перевіряємо, що ім'я нового користувача дорівнює очікуваній.
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert "avatar" in data


# #     if exist_user:
# #         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
def test_re_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.auth.email.send_email", mock_send_email)
    response = client.post("/auth/signup", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == messages.ACCOUNT_EXISTS


def test_email_not_confirmed_login(client):
    response = client.post("/auth/login", data={"username": user_data.get("email"),
                                                   "password": user_data.get("password")})
    print(response.json())
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.EMAIL_NOT_CONFIRMED


@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(UserModel).where(UserModel.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()
            session.refresh()

    response = client.post("/auth/login", data={"username": user_data.get("email"),
                                                   "password": user_data.get("password")})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data


def test_wrong_password_login(client):
    response = client.post("/auth/login", data={"username": user_data.get("email"),
                                                   "password": "password"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INVALID_PASSWORD


def test_wrong_email_login(client):
    response = client.post("/auth/login", data={"username": "email",
                                                   "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INVALID_EMAIL_ADDRESS


def test_validation_error(client):
    response = client.post("/auth/login",
                           data={"password": user_data.get("password")})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data