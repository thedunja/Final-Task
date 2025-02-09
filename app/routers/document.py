import io
import os
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path, Response
from pydantic import Field
from starlette.responses import StreamingResponse

from ..models import Project, Document
from ..database import SessionLocal
from .auth import get_current_user
from sqlalchemy.orm import Session
from starlette import status
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from fastapi.templating import Jinja2Templates
import boto3
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix='/documents',
    tags=['documents']
)

AWS_BUCKET = os.getenv("AWS_BUCKET")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION_NAME = os.getenv("AWS_REGION_NAME")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/document/{document_id}", status_code=status.HTTP_200_OK)
async def download_document(user: user_dependency,
                            db: db_dependency,
                            document_id: int = Path(gt=0)):

    document = db.query(Document).filter(Document.id == document_id).first()

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    document_name = document.document_name

    project_model = db.query(Project).filter(Project.id == document.project_id).filter(Project.owner_id == user.get('id')).first()

    if project_model is None:
        raise HTTPException(status_code=403, detail="You do not have access to this project")

    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )

    s3 = session.resource('s3')
    bucket = s3.Bucket(AWS_BUCKET)

    async def s3_download(key: str):
        try:
            return s3.Object(bucket_name=AWS_BUCKET, key=key).get()['Body'].read()
        except ClientError as err:
            logger.error(str(err))

    contents = await s3_download(key=document_name)
    return Response(
        content=contents,
        headers={
            'Content-Disposition': f'attachment; filename={document_name}',
            'Content-Type': 'apllication/octet-stream'
        }
    )


    ''' 
    async def s3_download(key: str):
        try:
            return s3.Object(bucket_name=AWS_BUCKET, key=key).get()['Body'].read()
        except ClientError as err:
            logger.error(str(err))

    contents = await s3_download(key=document_name)
    s3.Bucket(AWS_BUCKET).download_file(document_name, os.path.basename(document_name))
    return Response(
        content=contents,
        headers={
            'Content-Disposition': f'attachment; filename={document_name}',
            'Content-Type': 'apllication/octet-stream'
        }
    )


    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION_NAME
        )

        response = s3_client.get_object(Bucket=AWS_BUCKET, Key=document.file_path)
        file_stream = response['Body']

        return StreamingResponse(
            io.BytesIO(file_stream.read()),
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename={document.file_path.split("/")[-1]}'
            }
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e)) '''
