from fastapi.testclient import TestClient
from src.auth.models import ContactModel
from src.main import contacts_api

client = TestClient(contacts_api)


def test_get_contacts_route_without_db(client, get_token):
    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    
    client.get("/contacts", headers=headers)

    # Виконуємо запит GET для отримання контактів
    response = client.get("/contacts/", headers=headers)
    print(response.json())
    # Перевіряємо, чи отримали ми очікуваний статус код
    assert response.status_code == 200

    


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