import datetime
import jose.jwt
import fastapi
import fastapi.security
import passlib.context
import database
import auth.models


class Auth:
    HASH_CONTEXT = passlib.context.CryptContext(schemes=["bcrypt"])
    ALGORITM = "HS256"
    SECRET = "My secret key"
    oauth2_scheme = fastapi.security.OAuth2PasswordBearer("/auth/login")

    def verify_password(self, plain_password, hashed_password) -> bool:
        return self.HASH_CONTEXT.verify(plain_password, hashed_password)

    def get_password_hash(self, plain_password):
        return self.HASH_CONTEXT.hash(plain_password)

    async def create_access_token(self, payload: dict) -> str:
        to_encode = payload.copy()
        to_encode.update(
            {
                "exp": datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(minutes=15)
            }
        )
        encoded_jwt = jose.jwt.encode(to_encode, self.SECRET, algorithm=self.ALGORITM)
        return encoded_jwt

    async def create_refresh_token(self, payload: dict) -> str:
        to_encode = payload.copy()
        to_encode.update(
            {
                "exp": datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=7)
            }
        )
        encoded_jwt = jose.jwt.encode(to_encode, self.SECRET, algorithm=self.ALGORITM)
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
            payload = jose.jwt.decode(token, self.SECRET, algorithms=[self.ALGORITM])
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
            payload = jose.jwt.decode(token, Auth.SECRET, algorithms=[Auth.ALGORITM])
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
