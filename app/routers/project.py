import shutil
import os
from datetime import datetime
from typing import Annotated, List, Optional
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path, Request
from starlette import status
from ..models import Project, Document
from ..database import SessionLocal
from .auth import get_current_user
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import File, UploadFile
from PIL import Image
import io
import boto3
import magic
from uuid import uuid4
from loguru import logger
import psycopg2
from dotenv import load_dotenv

load_dotenv()


KB = 1024
MB = KB * 1024

SUPPORTED_FILE_TYPES = {
    'image/png': 'png',
    'image/jpg': 'jpg',
    'application/pdf': 'pdf'
}

AWS_BUCKET = os.getenv("AWS_BUCKET")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION_NAME = os.getenv("AWS_REGION_NAME")


templates = Jinja2Templates(directory="TodoApp/templates")

router = APIRouter(
    prefix='/projects',
    tags=['projects']
)


# Pydantic model for the request body
class ProjectRequest(BaseModel):
    name: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)


class S3UploadRequest(BaseModel):
    bucket_name: str
    file_path: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    project_id: int
    file_path: str
    file_type: str
    created_at: datetime


model_config = ConfigDict(from_attributes=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency,
                   db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')

    return db.query(Project).filter(Project.owner_id == user.get('id')).all()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(user: user_dependency, db: db_dependency, project_request: ProjectRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')

    project_model = Project(**project_request.model_dump(), owner_id=user.get('id'))

    db.add(project_model)
    db.commit()


@router.get("/project/{project_id}/info", status_code=status.HTTP_200_OK)
async def read_project(user: user_dependency,
                       db: db_dependency, project_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')
    project_model = db.query(Project).filter(Project.id == project_id).filter(Project.owner_id == user.get('id')).first()
    if project_model is not None:
        return project_model
    raise HTTPException(status_code=404, detail='Project not found')


@router.put("/project/{project_id}/info", status_code=status.HTTP_204_NO_CONTENT)
async def update_project(user: user_dependency,
                         db: db_dependency,
                         project_request: ProjectRequest,
                         project_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')

    project_model = db.query(Project).filter(Project.id == project_id).filter(Project.owner_id == user.get('id')).first()
    if project_model is None:
        raise HTTPException(status_code=404, detail='Project not found')
    project_model.name = project_request.name
    project_model.description = project_request.description

    db.add(project_model)
    db.commit()


@router.delete("project/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(user: user_dependency,
                         db: db_dependency, project_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')

    project_model = db.query(Project).filter(Project.id == project_id).filter(Project.owner_id == user.get('id')).first()
    if project_model is None:
        raise HTTPException(status_code=404, detail='Project not found')

    db.query(Project).filter(Project.id == project_id).delete()
    db.commit()


@router.get("/project/{project_id}/documents", response_model=List[DocumentResponse], status_code=status.HTTP_200_OK)
async def get_project_documents(user: user_dependency,
                                db: db_dependency,
                                project_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')

    project_model = db.query(Project).filter(Project.id == project_id).filter(Project.owner_id == user.get('id')).first()
    if project_model is None:
        raise HTTPException(status_code=404, detail='Project not found')

    documents = db.query(Document).filter(Document.project_id == project_id).all()
    if not documents:
        raise HTTPException(status_code=404, detail='No documents found for this project')

    return documents


@router.post("/project/{project_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_project_documents(user: user_dependency,
                                   db: db_dependency,
                                   project_id: int = Path(gt=0),
                                   s3_request: S3UploadRequest = Depends(),
                                   file: UploadFile = File(...)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication failed')

    project_model = db.query(Project).filter(Project.id == project_id).filter(Project.owner_id == user.get('id')).first()
    if project_model is None:
        raise HTTPException(status_code=404, detail='Project not found')

    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='File not found')
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION_NAME
        )
        # Set default file path if not provided
        if s3_request.file_path is None:
            s3_request.file_path = file.filename

        contents = await file.read()
        file_size = len(contents)

        if not 0 < file_size <= 1 * MB:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Supported file size is 0-1 MB')

        file_type = magic.from_buffer(buffer=contents, mime=True)
        if file_type not in SUPPORTED_FILE_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'File type {file_type} is not supported. Supported types are: {SUPPORTED_FILE_TYPES}')

        # Upload file to S3
        s3_client.upload_fileobj(file.file, s3_request.bucket_name, s3_request.file_path)

        # Save document info to database
        document = Document(
            project_id=project_id,
            document_name=file.filename,
            file_path=s3_request.file_path,
            file_type=file_type,
            created_at=datetime.utcnow()
        )
        db.add(document)
        db.commit()

        return {
            "message": f"File '{file.filename}' uploaded successfully to bucket '{s3_request.bucket_name}' at '{s3_request.file_path}'"}

    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="AWS credentials not found.")
    except PartialCredentialsError:
        raise HTTPException(status_code=403, detail="Incomplete AWS credentials.")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))






