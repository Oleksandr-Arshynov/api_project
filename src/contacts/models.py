import sqlalchemy as sa
import sqlalchemy.orm as orm
from datetime import datetime

from database import Base


class ContactModel(Base):
    """
    Represents a contact in the system.

    Attributes:
    id (int): The unique identifier for the contact.
    name (str): The name of the contact.
    surname (str): The surname of the contact.
    email (str): The email address of the contact.
    phone (str): The phone number of the contact.
    birthday (datetime): The birthday of the contact.
    other (str): Additional information about the contact.
    created_at (datetime): The datetime when the contact was created.
    updated_at (datetime): The datetime when the contact was last updated.
    user_id (int, optional): The foreign key referencing the user associated with the contact.
    user (User, optional): The user associated with the contact.

    """
    __tablename__ = "contacts"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    surname = sa.Column(sa.String)
    email = sa.Column(sa.String)
    phone = sa.Column(sa.String)
    birthday = sa.Column(sa.DateTime)
    other = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(
        sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=True)
    user = orm.relationship("User", backref="contacts", lazy="joined")
