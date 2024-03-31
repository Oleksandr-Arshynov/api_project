import sqlalchemy as sa
import sqlalchemy.orm as orm

class Base(orm.DeclarativeBase):
    pass

class ContactModel(Base):
    __tablename__ = "contacts"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    surname = sa.Column(sa.String)
    email = sa.Column(sa.String)
    phone = sa.Column(sa.String)
    birthday = sa.Column(sa.DateTime)
    other = sa.Column(sa.String)
