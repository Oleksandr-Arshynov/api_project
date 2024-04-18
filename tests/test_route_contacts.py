from unittest.mock import patch
from fastapi.testclient import TestClient
from src.auth.models import ContactModel
from src.main import contacts_api
from src.auth.service import auth_service


def test_get_contacts_route_without_db(client, get_token):
    with patch.object(auth_service, "cache") as redis_mock:  # Цей рядок мокує атрибут cache об'єкта auth_service.
        redis_mock.get.return_value = None
        token = get_token
        print("Token:", token)
        headers = {"Authorization": f"Bearer {token}"}
        print("Headers:", headers)

        # Now, make the request and check the response
        response = client.get("/contacts", headers=headers)
        print("Response:", response.status_code, response.text)

        # Add assertions here based on the response
        assert response.status_code == 200, response.text

   
   

    


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

# def test_create_contact(client, get_token):
#         token = get_token
#         headers = {"Authorization": f"Bearer {token}"}
    
# # Надсилає POST-запит до точки доступу для створення нового контакту. Запит включає заголовки та JSON-пакет, що представляє дані контакту.
#         response = client.post("/contacts/", headers=headers, json={
#             "name": "James II",
#             "surname": "Bond II",
#             "email": "jamesII@gmail.com",
#         })
#         assert response.status_code == 201, response.text  # Перевіряє, чи статус відповіді - 201, що вказує на успішне створення контакту.
#         data = response.json()  # Розбирає JSON-вміст відповіді в словник Python з ім'ям data
#         assert "id" in data  # Перевіряє, що відповідь містить ключ "id".
#         assert data[
#                    "first_name"] == "James II"  # Перевірка окремих полів створеного контакту, щоб переконатися, що вони відповідають наданим даним.
#         assert data["last_name"] == "Bond II"