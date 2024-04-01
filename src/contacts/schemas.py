import datetime
import pydantic

from auth.schemas import UserDb


class ContactResponseSchema(pydantic.BaseModel):
    id: int
    name: str
    surname: str
    email: str
    phone: str
    birthday: datetime.date
    other: str
    created_at: datetime.datetime | None
    updated_at: datetime.datetime | None
    current_user: UserDb | None
    
    class Config:
        arbitrary_types_allowed = True
    
class ContactRequestSchema(pydantic.BaseModel):
    name: str
    surname: str
    email: str
    phone: str
    birthday: datetime.date
    other: str
    
    class Config:
        arbitrary_types_allowed = True