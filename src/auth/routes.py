import pickle
import fastapi
import fastapi.security
import database

from fastapi_limiter.depends import RateLimiter
from fastapi import (
    Depends,
    HTTPException,
    UploadFile,
    File,
)
import cloudinary
import cloudinary.uploader

    

import auth.schemas
import auth.models
from auth.service import auth_service
from auth.email import send_email, send_email_reset

from conf.config import config

router = fastapi.APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=fastapi.status.HTTP_201_CREATED)
async def create_user(
    body: auth.schemas.User,
    bt: fastapi.BackgroundTasks,
    request: fastapi.Request,
    db=fastapi.Depends(database.get_db),
):
    """
    Create a new user account.

    Args:
        body (UserSchema): The user data to create the account.
        bt (BackgroundTasks): Background tasks for sending confirmation email.
        request (Request): The current request.
        db: The database session.

    Returns:
        UserSchema: The created user data.
        
    Raises:
        HTTPException: If the user already exists.
    """
    user = await auth_service.get_user_by_email(body.email, db)
    if user:
        raise fastapi.HTTPException(status_code=409, detail="User already exists")

    hashed_password = auth_service.get_password_hash(body.password)
    new_user = auth.models.User(
        username=body.username, email=body.email, hash_password=hashed_password
    )

    db.add(new_user)
    db.commit()

    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))

    return new_user


@router.post("/login")
async def login(
    body: fastapi.security.OAuth2PasswordRequestForm = fastapi.Depends(),
    db=fastapi.Depends(database.get_db),
) -> auth.schemas.Token:
    """
    Log in a user.

    Args:
        body (OAuth2PasswordRequestForm): The login credentials.
        db: The database session.

    Returns:
        Token: The access and refresh tokens.

    Raises:
        HTTPException: If the user is not found or credentials are incorrect.
    """
    user = (
        db.query(auth.models.User)
        .filter(auth.models.User.email == body.username)
        .first()
    )
    if not user:
        raise fastapi.HTTPException(status_code=401, detail="User not found")
    if not user:
        raise fastapi.HTTPException(status_code=401, detail="User not confirmed")
    verification = auth_service.verify_password(body.password, user.hash_password)
    if not verification:
        raise fastapi.HTTPException(status_code=400, detail="Incorrect credentials")

    refresh_token = await auth_service.create_access_token(
        payload={"sub": body.username}
    )
    access_token = await auth_service.create_access_token(
        payload={"sub": body.username}
    )

    user.refresh_token = refresh_token
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


get_refresh_token = fastapi.security.HTTPBearer()


@router.get("/refresh_token")
async def refresh_token(
    credentials: fastapi.security.HTTPAuthorizationCredentials = fastapi.Security(
        get_refresh_token
    ),
    db=fastapi.Depends(database.get_db),
):
    """
    Refresh an access token.

    Args:
        credentials (HTTPAuthorizationCredentials): The refresh token.
        db: The database session.

    Returns:
        Token: The new access and refresh tokens.

    Raises:
        HTTPException: If the token is invalid.
    """
    token = credentials.credentials
    username = await auth_service.decode_refresh_token(token)
    user = (
        db.query(auth.models.User)
        .filter(auth.models.User.refresh_token == token)
        .first()
    )
    if user.refresh_token != token:
        await auth_service.update_token(user, new_token=None, db=db)
        raise fastapi.HTTPException(status_code=400, detail="Invalid token")

    refresh_token = await auth_service.create_refresh_token(payload={"sub": username})
    access_token = await auth_service.create_access_token(payload={"sub": username})
    user.refresh_token = refresh_token
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db=fastapi.Depends(database.get_db)):
    """
    Confirm a user's email address.

    Args:
        token (str): The confirmation token.
        db: The database session.

    Returns:
        Dict[str, str]: A message confirming the email confirmation.

    Raises:
        HTTPException: If there is an error verifying the token.
    """
    email = await auth_service.get_email_from_token(token)
    user = await auth_service.get_user_by_email(email, db)
    if user is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await auth_service.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/request_email")
async def request_email(
    body: auth.schemas.RequestEmail,
    background_tasks: fastapi.BackgroundTasks,
    request: fastapi.Request,
    db=fastapi.Depends(database.get_db),
):
    """
    Request email confirmation.

    Args:
        body (RequestEmail): The user's email address.
        background_tasks (BackgroundTasks): Background tasks for sending the confirmation email.
        request (Request): The current request.
        db: The database session.

    Returns:
        Dict[str, str]: A message indicating that the email confirmation has been requested.
    """
    user = await auth_service.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": "Check your email for confirmation."}


@router.get(
    "/me",
    response_model=auth.schemas.UserDb,
    dependencies=[fastapi.Depends(RateLimiter(times=10, seconds=20))],
)
async def get_current_user(
    user: auth.models.User = fastapi.Depends(auth_service.get_current_user),
):
    """
    Get the current user.

    Args:
        user (User): The current user.

    Returns:
        UserSchema: The current user's data.
    """
    return user


cloudinary.config(
    cloud_name=config.CLD_NAME,
    api_key=config.CLD_API_KEY,
    api_secret=config.CLD_API_SECRET,
    secure=True,
)

@router.patch(
    "/avatar",
    response_model=auth.schemas.UserDb,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)
async def upgrade_avatar(
    file: UploadFile = File(),
    user: auth.models.User = fastapi.Depends(auth_service.get_current_user),
    db=fastapi.Depends(database.get_db),
):
    """
    Upgrade the user's avatar.

    Args:
        file (UploadFile): The new avatar image file.
        user (User): The current user.
        db: The database session.

    Returns:
        UserSchema: The updated user data with the new avatar URL.
    """
    public_id = f"Web19/{user.email}"
    print(public_id)
    res = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
    print(res)
    res_url = cloudinary.CloudinaryImage(public_id).build_url(
        width=250, height=250, crop="fill", version=res.get("version")
    )
    user = await auth_service.update_avatar_url(user.email, res_url, db)
    auth_service.cache.set(user.email, pickle.dumps(user))
    auth_service.cache.expire(user.email, 300)
    return user



