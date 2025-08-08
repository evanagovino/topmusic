from fastapi import FastAPI

from . import models
from .database import engine
from .routes import mobile_app, web, v2

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(mobile_app.router)
app.include_router(web.router)
app.include_router(v2.router)