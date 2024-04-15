from datetime import datetime
import sqlalchemy as sa
from database import Base


class User(Base):
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
    __table_args__ = {'extend_existing': True}

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
