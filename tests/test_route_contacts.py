from fastapi.testclient import TestClient
from src.main import contacts_api

client = TestClient(contacts_api)

from unittest.mock import Mock, patch

import pytest

from src.auth.service import auth_service


def test_get_contacts_route_without_db(client):
    # Фіктивні дані про контакти для тесту
    fake_contacts = [
        {"name": "John", "surname": "Doe", "email": "john@example.com"},
        {"name": "Jane", "surname": "Doe", "email": "jane@example.com"}
    ]

    # Ми можемо скористатися методом post для вставки фіктивних даних у базу даних
    for contact in fake_contacts:
        client.post("/contacts/", json=contact)

    # Виконуємо запит GET для отримання контактів
    response = client.get("/contacts/")

    # Перевіряємо, чи отримали ми очікуваний статус код
    assert response.status_code == 200

    # Перевіряємо, чи отримали ми очікувані дані про контакти
    data = response.json()
    assert len(data) == len(fake_contacts)


# def test_create_todo(client, get_token, monkeypatch):
#     with patch.object(auth_service, 'cache') as redis_mock:
#         redis_mock.get.return_value = None
#         token = get_token
#         headers = {"Authorization": f"Bearer {token}"}
#         response = client.post("api/todos", headers=headers, json={
#             "title": "test",
#             "description": "test",
#         })
#         assert response.status_code == 201, response.text
#         data = response.json()
#         assert "id" in data
#         assert data["title"] == "test"
#         assert data["description"] == "test"