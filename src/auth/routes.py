import datetime
import fastapi
import fastapi.security
import database

import auth.schemas
import auth.models
from auth.service import Auth

auth_service = Auth()

router = fastapi.APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", status_code=fastapi.status.HTTP_201_CREATED)
async def create_user(body: auth.schemas.User, db = fastapi.Depends(database.get_db)):
    user = db.query(auth.models.User).filter(auth.models.User.username == body.username).first()
    if user:
        raise fastapi.HTTPException(status_code=409, detail="User already exists")
    hashed_password = auth_service.get_password_hash(body.password)
    

    new_user = auth.models.User(
        username=body.username,
        hash_password=hashed_password,
    )
    db.add(new_user)
    db.commit()
    
    return new_user

@router.post("/login")
async def login(body: fastapi.security.OAuth2PasswordRequestForm = fastapi.Depends(),
                db = fastapi.Depends(database.get_db)) -> auth.schemas.Token:
    user = db.query(auth.models.User).filter(auth.models.User.username == body.username).first()
    if not user:
        raise fastapi.HTTPException(status_code=400, detail="User not found")
    
    verification = auth_service.verify_password(body.password, user.hash_password)
    if not verification:
        raise fastapi.HTTPException(status_code=400, detail="Incorrect credentials")
    
    refresh_token = await auth_service.create_access_token(payload={"sub": body.username})
    access_token = await auth_service.create_access_token(payload={"sub": body.username})
    
    user.refresh_token = refresh_token
    db.commit()
    
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
get_refresh_token = fastapi.security.HTTPBearer()
    
@router.get("/refresh_token")
async def refresh_token(credentials: fastapi.security.HTTPAuthorizationCredentials = fastapi.Security(get_refresh_token), db = fastapi.Depends(database.get_db)):
    token = credentials.credentials
    username = await auth_service.decode_refresh_token(token)
    user = db.query(auth.models.User).filter(auth.models.User.refresh_token == token).first()
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
