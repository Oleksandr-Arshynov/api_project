from datetime import datetime, timedelta, timezone
import jose.jwt
import fastapi
import fastapi.security
import passlib.context
from sqlalchemy import select
import database
import auth.models

from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors

from libgravatar import Gravatar
from conf.config import config


class Auth:
    HASH_CONTEXT = passlib.context.CryptContext(schemes=["bcrypt"])
    ALGORITHM = config.ALGORITHM
    SECRET = config.SECRET_KEY_JWT
    oauth2_scheme = fastapi.security.OAuth2PasswordBearer("/auth/login")

    def verify_password(self, plain_password, hashed_password) -> bool:
        return self.HASH_CONTEXT.verify(plain_password, hashed_password)

    def get_password_hash(self, plain_password):
        return self.HASH_CONTEXT.hash(plain_password)

    async def create_access_token(self, payload: dict) -> str:
        to_encode = payload.copy()
        to_encode.update({"exp": datetime.now(timezone.utc) + timedelta(minutes=15)})
        encoded_jwt = jose.jwt.encode(to_encode, self.SECRET, algorithm=self.ALGORITHM)
        return encoded_jwt

    async def create_refresh_token(self, payload: dict) -> str:
        to_encode = payload.copy()
        to_encode.update({"exp": datetime.now(timezone.utc) + timedelta(days=7)})
        encoded_jwt = jose.jwt.encode(to_encode, self.SECRET, algorithm=self.ALGORITHM)
        return encoded_jwt

    async def get_current_user(
        self,
        token: str = fastapi.Depends(oauth2_scheme),
        db=fastapi.Depends(database.get_db),
    ):

        credentials_exception = fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jose.jwt.decode(token, self.SECRET, algorithms=[self.ALGORITHM])
        except jose.ExpiredSignatureError:
            raise credentials_exception
        except jose.JWTError:
            raise credentials_exception

        email = payload.get("sub")
        if email is None:
            raise credentials_exception

        user = (
            db.query(auth.models.User)
            .filter(auth.models.User.username == email)
            .first()
        )
        if user is None:
            raise credentials_exception
        return user

    async def decode_refresh_token(self, token: str) -> str:
        try:
            payload = jose.jwt.decode(token, Auth.SECRET, algorithms=[Auth.ALGORITHM])
            return payload.get("sub")
        except jose.ExpiredSignatureError:
            raise fastapi.HTTPException(status_code=401, detail="Token has expired")
        except (jose.JWTError, ValueError):
            raise fastapi.HTTPException(
                status_code=401, detail="Could not validate credentials"
            )

    async def update_token(
        user: auth.models.User, token: str | None, db=fastapi.Depends(database.get_db)
    ):
        user.refresh_token = token
        await db.commit()

    async def get_user_by_email(self, email: str, db=fastapi.Depends(database.get_db)):
        stmt = select(auth.models.User).filter_by(email=email)
        user = db.execute(stmt)
        user = user.scalar_one_or_none()
        return user

    async def confirmed_email(
        self, email: str, db=fastapi.Depends(database.get_db)
    ) -> None:
        user = await Auth.get_user_by_email(self, email=email, db=db)
        user.confirmed = True
        db.commit()

    def create_email_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jose.jwt.encode(to_encode, self.SECRET, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        try:
            payload = jose.jwt.decode(token, self.SECRET, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except jose.JWTError as e:
            print(e)
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            )

    async def create_user(
        self, body: auth.models.User, db=fastapi.Depends(database.get_db)
    ):
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as err:
            print(err)

        new_user = auth.models.User(**body.model_dump(), avatar=avatar)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user


auth_service = Auth()
