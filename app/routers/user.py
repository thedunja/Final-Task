from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status
from ..models import Project, User
from ..database import SessionLocal
from .auth import get_current_user
from passlib.context import CryptContext


class PasswordVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)


router = APIRouter(
    prefix='/user',
    tags=['user']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@router.get("/", status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency,
                   db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')
    user_model = db.query(User).filter(User.id == user.get('id')).first()
    if user_model is None:
        raise HTTPException(status_code=401, detail='User not found')
    return user_model


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency,
                          db: db_dependency,
                          user_verification: PasswordVerification):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')
    user_model = db.query(User).filter(User.id == user.get('id')).first()
    if user_model is None:
        raise HTTPException(status_code=401, detail='User not found')
    if not bcrypt_context.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail='Error on password change')
    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)

    db.add(user_model)
    db.commit()


@router.put("/phonenumber/{phone_number}", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_phone_number(db: db_dependency,
                                   user: user_dependency,
                                   phone_number: str = Path(min_length=3)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')
    user_model = db.query(User).filter(User.id == user.get('id')).first()
    user_model.phone_number = phone_number

    db.add(user_model)
    db.commit()

