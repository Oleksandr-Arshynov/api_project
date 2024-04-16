from datetime import datetime
import sqlalchemy as sa
import sqlalchemy.orm as orm
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserModel(Base):
    """
    Represents a user in the system.

    Attributes:
        id (int): The unique identifier for the user.
        username (str): The username of the user.
        email (str): The email address of the user.
        avatar (str, optional): The URL of the user's avatar image.
        hash_password (str): The hashed password of the user.
        refresh_token (str): The refresh token used for authentication.
        created_at (datetime): The datetime when the user account was created.
        updated_at (datetime): The datetime when the user account was last updated.
        confirmed (bool, optional): Indicates whether the user's email address has been confirmed.
    """

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(30))
    email = sa.Column(sa.String(255), unique=True)
    avatar = sa.Column(sa.String(255), nullable=True)
    hash_password = sa.Column(sa.String)
    refresh_token = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(
        sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    confirmed = sa.Column(sa.BOOLEAN, default=False, nullable=True)



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
    user (UserModel, optional): The user associated with the contact.

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
    user = orm.relationship("UserModel", backref="contacts", lazy="joined")
