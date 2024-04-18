from datetime import datetime, timedelta, timezone
import pickle
import unittest
import jose.jwt
import fastapi
import fastapi.security
import passlib.context
import redis
from sqlalchemy import select
import database
import auth.models

from libgravatar import Gravatar
from conf.config import config


class Auth:
    HASH_CONTEXT = passlib.context.CryptContext(schemes=["bcrypt"])
    ALGORITHM = config.ALGORITHM
    SECRET = config.SECRET_KEY_JWT
    oauth2_scheme = fastapi.security.OAuth2PasswordBearer("/auth/login")
    cache = redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )

    def verify_password(self, plain_password, hashed_password) -> bool:
        """Verify the password against its hash.

        Args:
            plain_password (str): The plain password.
            hashed_password (str): The hashed password.

        Returns:
            bool: True if the passwords match, False otherwise.
        """
        return self.HASH_CONTEXT.verify(plain_password, hashed_password)
    
    

    def get_password_hash(self, plain_password):
        """Get the hash of a password.

        Args:
            plain_password (str): The plain password.

        Returns:
            str: The hashed password.
        """
        return self.HASH_CONTEXT.hash(plain_password)

    async def create_access_token(self, payload: dict) -> str:
        """Create an access token.

        Args:
            payload (dict): The payload to encode into the token.

        Returns:
            str: The access token.
        """
        to_encode = payload.copy()
        to_encode.update({"exp": datetime.now(timezone.utc) + timedelta(minutes=15)})
        encoded_jwt = jose.jwt.encode(to_encode, self.SECRET, algorithm=self.ALGORITHM)
        return encoded_jwt

    async def create_refresh_token(self, payload: dict) -> str:
        """Create a refresh token.

        Args:
            payload (dict): The payload to encode into the token.

        Returns:
            str: The refresh token.
        """
        to_encode = payload.copy()
        to_encode.update({"exp": datetime.now(timezone.utc) + timedelta(days=7)})
        encoded_jwt = jose.jwt.encode(to_encode, self.SECRET, algorithm=self.ALGORITHM)
        return encoded_jwt

    async def get_current_user(
        self,
        token: str = fastapi.Depends(oauth2_scheme),
        db=fastapi.Depends(database.get_db),
    ):
        """Get the current authenticated user.

        Args:
            token (str, optional): The JWT token. Defaults to fastapi.Depends(oauth2_scheme).
            db: The database session.

        Returns:
            auth.models.User: The current user.
        """

        credentials_exception = fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"Authenticate": "Bearer"},
        )
        try:
            payload = jose.jwt.decode(token, self.SECRET, algorithms=[self.ALGORITHM])
        except jose.ExpiredSignatureError:
            raise credentials_exception
        except jose.JWTError:
            raise credentials_exception

        email = payload.get("sub")
        print(f"Email {email}")
        
        if email is None:
            raise credentials_exception

        user_hash = str(email)
        user = self.cache.get(user_hash)
        
        print(f"User {user}")

        if user is None:
            print("User from db")
            user = (
                db.query(auth.models.UserModel)
                .filter(auth.models.UserModel.username == user_hash)
                .first()
            )
            print(f"User {user}")
            
            if user is None:
                raise credentials_exception
            self.cache.set(user_hash, pickle.dumps(user))
            self.cache.expire(user_hash, 300)
        else:
            print("User from cache")
            user = pickle.loads(user)
            print(user)
        return user

    async def decode_refresh_token(self, token: str) -> str:
        """Decode a refresh token.

        Args:
            token (str): The refresh token.

        Returns:
            str: The decoded token.
        """
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
        user: auth.models.UserModel, token: str | None, db=fastapi.Depends(database.get_db)
    ):
        """Update the user's refresh token.

        Args:
            user (auth.models.User): The user.
            token (str | None): The new refresh token, or None to clear it.
            db: The database session.
        """
        user.refresh_token = token
        await db.commit()

    async def get_user_by_email(self, email: str, db=fastapi.Depends(database.get_db)):
        """Get a user by email.

        Args:
            email (str): The user's email.
            db: The database session.

        Returns:
            auth.models.User: The user.
        """
        stmt = select(auth.models.UserModel).filter_by(email=email)
        user = db.execute(stmt)
        user = user.scalar_one_or_none()
        return user

    async def confirmed_email(
        self, email: str, db=fastapi.Depends(database.get_db)
    ) -> None:
        """Confirm a user's email address.

        Args:
            email (str): The user's email.
            db: The database session.
        """
        user = await Auth.get_user_by_email(self, email=email, db=db)
        user.confirmed = True
        db.commit()

    def create_email_token(self, data: dict):
        """Create an email verification token.

        Args:
            data (dict): The data to encode into the token.

        Returns:
            str: The encoded token.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jose.jwt.encode(to_encode, self.SECRET, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        """Get the email from an email verification token.

        Args:
            token (str): The token.

        Returns:
            str: The email.
        """
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
        self, body: auth.models.UserModel, db=fastapi.Depends(database.get_db)
    ):
        """Create a new user.

        Args:
            body (auth.models.User): The user data.
            db: The database session.

        Returns:
            auth.models.User: The created user.
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as err:
            print(err)

        new_user = auth.models.UserModel(**body.model_dump(), avatar=avatar)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    async def update_avatar_url(
        self, email: str, url: str | None, db=fastapi.Depends(database.get_db)
    ):
        """Update a user's avatar URL.

        Args:
            email (str): The user's email.
            url (str | None): The new avatar URL, or None to clear it.
            db: The database session.

        Returns:
            auth.models.User: The updated user.
        """
        user = (
            db.query(auth.models.UserModel)
            .filter(auth.models.UserModel.username == email)
            .first()
        )
        user.avatar = url
        db.commit()
        db.refresh(user)
        return user



auth_service = Auth()

