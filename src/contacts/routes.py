from datetime import datetime, timedelta
import fastapi
from fastapi.params import Query 
from auth.models import User
from auth.service import Auth
import contacts.schemas as schemas
import contacts.models as models
from database import get_db

router = fastapi.APIRouter(prefix="/contacts", tags=["contacts"])

auth_service = Auth()

@router.get("/get")
async def get_contact(
    id: int = None,
    name: str = Query(None),
    surname: str = Query(None),
    email: str = Query(None),
    db=fastapi.Depends(get_db),
    current_user: User = fastapi.Depends(auth_service.get_current_user)
):
    query = db.query(models.ContactModel).filter(models.ContactModel.user_id == current_user.id)
    

    if id is not None:
        query = query.filter(models.ContactModel.id == id)
    if name:
        query = query.filter(models.ContactModel.name == name)
    if surname:
        query = query.filter(models.ContactModel.surname == surname)
    if email:
        query = query.filter(models.ContactModel.email == email)

    contact = query.first()
    if not contact:
        return {"error": "Contact not found"}

    return contact


@router.get("/")
async def get_contacts(db = fastapi.Depends(get_db), current_user: User = fastapi.Depends(auth_service.get_current_user)):
    contacts = db.query(models.ContactModel).filter(models.ContactModel.user_id == current_user.id).all()
    
    return contacts


@router.post("/")
async def create_contact(contact: schemas.ContactRequestSchema, db = fastapi.Depends(get_db), current_user: User = fastapi.Depends(auth_service.get_current_user)):
    new_contact = models.ContactModel(
        name=contact.name,
        surname=contact.surname,
        email=contact.email,
        phone=contact.phone,
        birthday=contact.birthday,
        user_id=current_user.id 
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
    db = fastapi.Depends(get_db),
    current_user: User = fastapi.Depends(auth_service.get_current_user)
):
    db_contact = db.query(models.ContactModel).filter(models.ContactModel.id == id).first()

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
async def delete_contact(id: int, db = fastapi.Depends(get_db), current_user: User = fastapi.Depends(auth_service.get_current_user)):
    contact = db.query(models.ContactModel).filter(models.ContactModel.id == id).first()
    if contact and contact.user_id == current_user.id:
        db.delete(contact)
        db.commit()
        return contact
    return {"error": "Contact not found or does not belong to the current user"}

@router.get("/upcoming_birthdays")
async def get_upcoming_birthdays(db=fastapi.Depends(get_db), current_user: User = fastapi.Depends(auth_service.get_current_user)):
    current_date = datetime.now()
    next_week = current_date + timedelta(days=8)

    contacts = db.query(models.ContactModel).filter(
        models.ContactModel.birthday.between(current_date, next_week)
    ).all()
    print(contacts)

    return contacts


    