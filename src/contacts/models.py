import sqlalchemy as sa
import sqlalchemy.orm as orm
from datetime import datetime

from database import Base

class ContactModel(Base):
    __tablename__ = "contacts"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    surname = sa.Column(sa.String)
    email = sa.Column(sa.String)
    phone = sa.Column(sa.String)
    birthday = sa.Column(sa.DateTime)
    other = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=True)
    user = orm.relationship("User", backref="contacts", lazy="joined")