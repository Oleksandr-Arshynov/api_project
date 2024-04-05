import datetime
import fastapi
import fastapi.security
import database

import auth.schemas
import auth.models
from auth.service import auth_service, send_email


router = fastapi.APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=fastapi.status.HTTP_201_CREATED)
async def create_user(
    body: auth.schemas.User,
    bt: fastapi.BackgroundTasks,
    request: fastapi.Request,
    db=fastapi.Depends(database.get_db),
):
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
    user = await auth_service.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": "Check your email for confirmation."}


@router.get("/{username}")
async def request_email(username: str, response: fastapi.Response, db=fastapi.Depends(database.get_db)):
    print("__________")
    print(f"{username} зберігаємо")
    print("__________")
    return fastapi.responses.FileResponse("src/static/open_chek.png", media_type="image/png", content_disposition_type="inline")
