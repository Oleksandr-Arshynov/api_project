from datetime import datetime
import sqlalchemy as sa
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(30), unique=True)
    hash_password = sa.Column(sa.String)
    refresh_token = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)