import pydantic


class User(pydantic.BaseModel):
    username: str
    password: str
    email: str


class UserDb(pydantic.BaseModel):
    id: int
    username: str
    email: str
    hash_password: str
    avatar: str


class Token(pydantic.BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RequestEmail(pydantic.BaseModel):
    email: str
