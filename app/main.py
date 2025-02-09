from fastapi import FastAPI
from .routers import auth, project, admin, user, document
from .models import Base
from .database import engine


app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/healthy")
def health_check():
    return {'status': 'Healthy'}


app.include_router(auth.router)
app.include_router(project.router)
app.include_router(document.router)
app.include_router(admin.router)
app.include_router(user.router)
