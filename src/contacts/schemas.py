import datetime
import pydantic


class ContactResponseSchema(pydantic.BaseModel):
    id: int
    name: str
    surname: str
    email: str
    phone: str
    birthday: datetime.date
    other: str
    
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