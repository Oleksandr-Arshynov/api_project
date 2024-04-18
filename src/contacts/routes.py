from datetime import datetime, timedelta
import fastapi
from fastapi.params import Query
from auth.models import UserModel, ContactModel
from auth.service import Auth
import contacts.schemas as schemas
from database import get_db


router = fastapi.APIRouter(prefix="/contacts", tags=["contacts"])

auth_service = Auth()


@router.get("/get")
async def get_contact_route(
    id: int = None,
    name: str = Query(None),
    surname: str = Query(None),
    email: str = Query(None),
    db=fastapi.Depends(get_db),
    current_user: UserModel = fastapi.Depends(auth_service.get_current_user),
):
    """
    Get a single contact by ID or by name, surname, or email.

    Args:
        id (int, optional): The ID of the contact.
        name (str, optional): The name of the contact.
        surname (str, optional): The surname of the contact.
        email (str, optional): The email address of the contact.
        db: The database session.
        current_user: The current authenticated user.

    Returns:
        dict or models.ContactModel: The contact information or an error message.
    """
    query = db.query(ContactModel).filter(
        ContactModel.user_id == current_user.id
    )

    if id is not None:
        query = query.filter(ContactModel.id == id)
    if name:
        query = query.filter(ContactModel.name == name)
    if surname:
        query = query.filter(ContactModel.surname == surname)
    if email:
        query = query.filter(ContactModel.email == email)

    contact = query.first()
    if not contact:
        return {"error": "Contact not found"}

    return contact


@router.get("")
async def get_contacts_route(
    db=fastapi.Depends(get_db),
    current_user: UserModel = fastapi.Depends(auth_service.get_current_user),
):
    """
    Get all contacts belonging to the current user.

    Args:
        db: The database session.
        current_user: The current authenticated user.

    Returns:
        List[models.ContactModel]: The list of contacts belonging to the current user.
    """
    contacts = (
        db.query(ContactModel)
        .filter(ContactModel.user_id == current_user.id)
        .all()
    )

    return contacts


@router.post("/")
async def create_contact(
    contact: schemas.ContactRequestSchema,
    db=fastapi.Depends(get_db),
    current_user: UserModel = fastapi.Depends(auth_service.get_current_user),
):
    """
    Create a new contact for the current user.

    Args:
        contact (schemas.ContactRequestSchema): The contact details to be created.
        db: The database session.
        current_user: The current authenticated user.

    Returns:
        models.ContactModel: The newly created contact.
    """
    new_contact = ContactModel(
        name=contact.name,
        surname=contact.surname,
        email=contact.email,
        phone=contact.phone,
        birthday=contact.birthday,
        user_id=current_user.id,
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)

    new_contact.user.hash_password = None
    new_contact.user.refresh_token = None
    return new_contact


@router.put("/{id}")
async def update_contact(
    id: int,
    contact: schemas.ContactRequestSchema,
    db=fastapi.Depends(get_db),
    current_user: UserModel = fastapi.Depends(auth_service.get_current_user),
):
    """
    Update an existing contact belonging to the current user.

    Args:
        id (int): The ID of the contact to be updated.
        contact (schemas.ContactRequestSchema): The updated contact details.
        db: The database session.
        current_user: The current authenticated user.

    Returns:
        dict: A message indicating the success or failure of the operation.
    """
    db_contact = (
        db.query(ContactModel).filter(ContactModel.id == id).first()
    )

    if db_contact and db_contact.user_id == current_user.id:
        db_contact.name = contact.name
        db_contact.surname = contact.surname
        db_contact.email = contact.email
        db_contact.phone = contact.phone
        db_contact.birthday = contact.birthday
        db_contact.other = contact.other

        db.commit()
        return {"message": "Contact updated successfully"}

    return {"error": "Contact not found or does not belong to the current user"}


@router.delete("/{id}")
async def delete_contact(
    id: int,
    db=fastapi.Depends(get_db),
    current_user: UserModel = fastapi.Depends(auth_service.get_current_user),
):
    """
    Delete an existing contact belonging to the current user.

    Args:
        id (int): The ID of the contact to be deleted.
        db: The database session.
        current_user: The current authenticated user.

    Returns:
        dict or models.ContactModel: The deleted contact or an error message.
    """
    contact = db.query(ContactModel).filter(ContactModel.id == id).first()
    if contact and contact.user_id == current_user.id:
        db.delete(contact)
        db.commit()
        return contact
    return {"error": "Contact not found or does not belong to the current user"}


@router.get("/upcoming_birthdays")
async def get_upcoming_birthdays(
    db=fastapi.Depends(get_db),
    current_user: UserModel = fastapi.Depends(auth_service.get_current_user),
):
    """
    Get contacts with birthdays within the next week for the current user.

    Args:
        db: The database session.
        current_user: The current authenticated user.

    Returns:
        List[models.ContactModel]: The list of contacts with upcoming birthdays.
    """
    current_date = datetime.now()
    next_week = current_date + timedelta(days=8)

    contacts = (
        db.query(ContactModel)
        .filter(ContactModel.birthday.between(current_date, next_week))
        .all()
    )
    print(contacts)

    return contacts
